from vid2text.cache import Cache, text_key


def test_open_creates_dirs(tmp_path):
    Cache(tmp_path / "cache")
    assert (tmp_path / "cache" / "audio").is_dir()
    assert (tmp_path / "cache" / "text").is_dir()


def test_text_key_includes_model():
    assert text_key("a1b2c3d4e5f67890", "paraformer") == "a1b2c3d4e5f67890-paraformer"


def test_write_and_hit(tmp_path):
    c = Cache(tmp_path / "cache")
    key = text_key("a1b2c3d4e5f67890", "paraformer")
    c.write_text(key, "识别结果文本")
    assert c.read_text(key) == "识别结果文本"


def test_miss_returns_none(tmp_path):
    c = Cache(tmp_path / "cache")
    assert c.read_text(text_key("a1b2c3d4e5f67890", "paraformer")) is None


def test_different_models_do_not_collide(tmp_path):
    c = Cache(tmp_path / "cache")
    c.write_text(text_key("a1b2c3d4e5f67890", "paraformer"), "中文结果")
    c.write_text(text_key("a1b2c3d4e5f67890", "sensevoice"), "EN result")
    assert c.read_text(text_key("a1b2c3d4e5f67890", "paraformer")) == "中文结果"
    assert c.read_text(text_key("a1b2c3d4e5f67890", "sensevoice")) == "EN result"


def test_corrupt_file_treated_as_miss(tmp_path):
    c = Cache(tmp_path / "cache")
    key = text_key("a1b2c3d4e5f67890", "paraformer")
    c.write_text(key, "x")
    for p in (tmp_path / "cache" / "text").glob("*"):
        p.unlink()
    assert c.read_text(key) is None


def test_list_and_clear(tmp_path):
    c = Cache(tmp_path / "cache")
    c.write_text(text_key("a1b2c3d4e5f67890", "paraformer"), "a")
    c.write_text(text_key("a1b2c3d4e5f67890", "sensevoice"), "b")
    entries = c.list_entries()
    assert len(entries) == 2
    c.clear()
    assert c.list_entries() == []
