from config.credentials import load_fernet_keys


def test_fernet_key_file_takes_precedence_over_environment(tmp_path):
    primary, previous = "primary-key", "previous-key"
    credential = tmp_path / "fernet-keys"
    credential.write_text(f"{primary}\n{previous}\n")

    keys = load_fernet_keys(
        {
            "FERNET_KEYS": "environment-key",
            "FERNET_KEYS_FILE": str(credential),
        }
    )

    assert keys == [primary, previous]


def test_systemd_credential_directory_is_supported(tmp_path):
    credential = tmp_path / "fernet-keys"
    credential.write_text("systemd-key\n")

    assert load_fernet_keys({"CREDENTIALS_DIRECTORY": str(tmp_path)}) == ["systemd-key"]


def test_environment_keys_remain_a_local_development_fallback():
    assert load_fernet_keys({"FERNET_KEYS": "first, second"}) == ["first", "second"]
