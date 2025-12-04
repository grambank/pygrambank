def test_Issue(api):
    issue = api.issues[0]
    assert issue.html.startswith('<p>')
    assert list(issue.iter_urls())
    assert list(issue.iter_issue_links())
    assert next(issue.iter_links()) == ('http://example.com', 'ex')
    assert next(issue.iter_images()) == ('http://example.org/image.jpg', 'alt')
