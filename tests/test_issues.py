
def test_Issue(api):
    issue = api.issues[0]
    assert issue.html.startswith('<p>')
    assert list(issue.iter_urls())
    assert list(issue.iter_issue_links())
    assert list(issue.iter_links())[0] == ('http://example.com', 'ex')
    assert list(issue.iter_images())[0] == ('http://example.org/image.jpg', 'alt')
