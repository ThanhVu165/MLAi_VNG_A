from ui.presentation import escape_html, local_time, readable_text, reply_text


def test_ui_uses_vietnamese_time_and_complete_guard_explanations() -> None:
    assert local_time("2026-09-22T01:02:03Z") == "08:02:03 ngày 22/09/2026"
    text = readable_text("R8a groundedness_failed:citation_ratio")
    assert "một số nội dung chưa được dẫn nguồn" in text
    assert "R8a" not in text and "_ratio" not in text
    assert reply_text("Lệ phí 150.000 đồng. [fee]", ["fee"]) == "Lệ phí 150.000 đồng. [1]"


def test_dynamic_html_is_escaped_at_the_render_boundary() -> None:
    payload = '<img src=x onerror="alert(1)"> & "quoted"'
    assert escape_html(payload) == (
        "&lt;img src=x onerror=&quot;alert(1)&quot;&gt; &amp; &quot;quoted&quot;"
    )
