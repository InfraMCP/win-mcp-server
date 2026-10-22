"""Tests for Keychain credential lookup."""

from unittest.mock import patch

from win_mcp_server import credentials


# A realistic `security dump-keychain` fragment holding two win-mcp entries
# (in the order attributes appear: acct before svce) plus an unrelated item.
DUMP_KEYCHAIN_OUTPUT = '''\
keychain: "/Users/x/Library/Keychains/login.keychain-db"
attributes:
    0x00000007 <blob>="Some Website"
    "acct"<blob>="someone@example.com"
    "svce"<blob>="other-service"
attributes:
    0x00000007 <blob>="win-mcp"
    "acct"<blob>="supervisore@macnil.it"
    "svce"<blob>="win-mcp"
attributes:
    0x00000007 <blob>="win-mcp"
    "acct"<blob>="enzo@10.211.55.7"
    "svce"<blob>="win-mcp"
'''


class _FakeCompleted:
    def __init__(self, stdout):
        self.stdout = stdout
        self.returncode = 0


def test_list_accounts_enumerates_all_win_mcp_entries():
    """dump-keychain parsing returns every account for the service, not one."""
    with patch("win_mcp_server.credentials.subprocess.run",
               return_value=_FakeCompleted(DUMP_KEYCHAIN_OUTPUT)):
        accounts = credentials.keychain_list_accounts("win-mcp")

    assert accounts == ["supervisore@macnil.it", "enzo@10.211.55.7"]


def test_list_accounts_ignores_other_services():
    """Accounts belonging to a different service are not returned."""
    with patch("win_mcp_server.credentials.subprocess.run",
               return_value=_FakeCompleted(DUMP_KEYCHAIN_OUTPUT)):
        accounts = credentials.keychain_list_accounts("win-mcp")

    assert "someone@example.com" not in accounts


def test_get_credentials_picks_correct_account_with_multiple_entries():
    """Regression for #3: the right domain's credentials are returned even
    when several win-mcp entries exist (previously only the default was seen)."""
    stored = {
        "supervisore@macnil.it": "macnil-pass",
        "enzo@10.211.55.7": "vm-pass",
    }

    with patch.object(credentials, "keychain_list_accounts",
                       return_value=list(stored)), \
         patch.object(credentials, "keychain_check_expired", return_value=False), \
         patch.object(credentials, "keychain_get_password",
                      side_effect=lambda svc, acct: stored.get(acct)):
        # Parallels VM reached by IP -> domain is the full IP 10.211.55.7
        username, password = credentials.get_credentials("10.211.55.7")

    assert (username, password) == ("enzo", "vm-pass")


def test_get_credentials_skips_expired_entries():
    """Expired cached entries are ignored so they get re-prompted (TTL on read)."""
    with patch.object(credentials, "keychain_list_accounts",
                      return_value=["enzo@10.211.55.7"]), \
         patch.object(credentials, "keychain_check_expired", return_value=True), \
         patch.object(credentials, "keychain_get_password", return_value="vm-pass"), \
         patch.object(credentials, "prompt_credentials_gui",
                      return_value=("prompted", "new-pass")) as prompt, \
         patch.object(credentials, "keychain_set_password"):
        username, password = credentials.get_credentials("10.211.55.7")

    prompt.assert_called_once()
    assert (username, password) == ("prompted", "new-pass")


# --- get_domain_from_hostname -------------------------------------------------

def test_domain_from_ipv4_uses_full_address():
    """Regression: an IPv4 host must not be split like an FQDN."""
    assert credentials.get_domain_from_hostname("10.211.55.7") == "10.211.55.7"


def test_domain_from_ipv6_uses_full_address():
    assert credentials.get_domain_from_hostname("fe80::1") == "fe80::1"


def test_domain_from_fqdn_uses_parent_domain():
    assert credentials.get_domain_from_hostname("server.domain.local") == "domain.local"


def test_domain_from_bare_hostname_appends_local():
    assert credentials.get_domain_from_hostname("winbox") == "winbox.local"


# --- _username_for_account ----------------------------------------------------

def test_username_for_account_matches_at_format():
    assert credentials._username_for_account("enzo@10.211.55.7", "10.211.55.7") == "enzo"


def test_username_for_account_matches_backslash_format():
    assert credentials._username_for_account("CORP\\enzo", "CORP") == "enzo"


def test_username_for_account_rejects_other_domain():
    assert credentials._username_for_account("enzo@other.local", "10.211.55.7") is None


def test_username_for_account_rejects_substring_domain():
    # "55.7" is a substring but not the account's domain -> must not match.
    assert credentials._username_for_account("enzo@10.211.55.7", "55.7") is None


# --- keychain_check_expired ---------------------------------------------------

class _FakeCompletedOut:
    def __init__(self, stdout):
        self.stdout = stdout


def test_check_expired_parses_icmt_future_expiry():
    """A future expiry epoch in the icmt attribute means NOT expired."""
    out = '    "icmt"<blob>="expires:9999999999"\n'
    with patch("win_mcp_server.credentials.subprocess.run",
               return_value=_FakeCompletedOut(out)):
        assert credentials.keychain_check_expired("win-mcp", "enzo@10.211.55.7") is False


def test_check_expired_parses_icmt_past_expiry():
    out = '    "icmt"<blob>="expires:1"\n'
    with patch("win_mcp_server.credentials.subprocess.run",
               return_value=_FakeCompletedOut(out)):
        assert credentials.keychain_check_expired("win-mcp", "enzo@10.211.55.7") is True


def test_check_expired_assumes_expired_when_command_fails():
    import subprocess as _sp
    with patch("win_mcp_server.credentials.subprocess.run",
               side_effect=_sp.CalledProcessError(2, "security")):
        assert credentials.keychain_check_expired("win-mcp", "missing") is True


# --- clear_cached_credentials / credentials_available -------------------------

def test_clear_cached_credentials_removes_all_matching_entries():
    """Every account for the domain is deleted, not just the first (multi-entry)."""
    deleted = []

    def fake_run(cmd, *a, **k):
        if cmd[:2] == ["security", "delete-generic-password"]:
            deleted.append(cmd[cmd.index("-a") + 1])
        return _FakeCompletedOut("")

    with patch.object(credentials, "keychain_list_accounts",
                      return_value=["enzo@10.211.55.7", "admin@10.211.55.7",
                                    "other@macnil.it"]), \
         patch("win_mcp_server.credentials.subprocess.run", side_effect=fake_run):
        cleared = credentials.clear_cached_credentials("10.211.55.7")

    assert cleared is True
    assert deleted == ["enzo@10.211.55.7", "admin@10.211.55.7"]


def test_credentials_available_true_when_valid_entry_exists():
    with patch.object(credentials, "keychain_list_accounts",
                      return_value=["enzo@10.211.55.7"]), \
         patch.object(credentials, "keychain_check_expired", return_value=False):
        assert credentials.credentials_available("10.211.55.7") is True


def test_credentials_available_false_when_only_expired():
    with patch.object(credentials, "keychain_list_accounts",
                      return_value=["enzo@10.211.55.7"]), \
         patch.object(credentials, "keychain_check_expired", return_value=True):
        assert credentials.credentials_available("10.211.55.7") is False
