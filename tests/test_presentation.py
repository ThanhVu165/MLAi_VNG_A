from ui.presentation import local_time, readable_text, reply_text


def test_ui_uses_vietnamese_time_and_complete_guard_explanations() -> None:
    assert local_time("2026-09-22T01:02:03Z") == "08:02:03 ngày 22/09/2026"
    text = readable_text("R8a groundedness_failed:citation_ratio")
    assert "một số nội dung chưa được dẫn nguồn" in text
    assert "R8a" not in text and "_ratio" not in text
    assert reply_text("Lệ phí 150.000 đồng. [fee]", ["fee"]) == "Lệ phí 150.000 đồng. [1]"
