from trackers_integration.models import ApiToken


def personal_api_token(issue_tracker):
    # usually as part of automated tests
    if not issue_tracker.request:
        return None

    token = ApiToken.objects.filter(
        owner=issue_tracker.request.user, base_url=issue_tracker.bug_system.base_url
    ).first()
    if token:
        return (token.api_username, token.api_password)

    return None
