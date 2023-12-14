import pytest
from unittest.mock import patch
from notifier.notifier import send_plan_content_email, check_and_send_reminders

@pytest.fixture
def mock_smtp():
    with patch('smtplib.SMTP') as mock_smtp:
        yield mock_smtp


def test_send_plan_content_email_success(mock_smtp):
    send_plan_content_email("test@example.com", "Test content")

    # Ensure sendmail was called
    assert mock_smtp.return_value.sendmail.called
    assert mock_smtp.return_value.quit.called

    # Extract the arguments passed to sendmail
    args = mock_smtp.return_value.sendmail.call_args[0]

    # args[0] is the sender's email, args[1] is the receiver's email, and args[2] is the email body
    receiver_email = args[1]
    email_body = args[2]

    assert receiver_email == "test@example.com"
    assert "Test content" in email_body

def test_send_plan_content_email_failure(mock_smtp):
    # an exception is simulated to occur when the sendmail method of the SMTP server object is called
    mock_smtp.return_value.sendmail.side_effect = Exception("SMTP error")
    send_plan_content_email("test@example.com", "Test content")
    assert mock_smtp.return_value.sendmail.called == True
    assert mock_smtp.return_value.quit.called == False

@patch('notifier.notifier.plans_collection')
def test_check_and_send_reminders(mock_plans_collection):
    mock_plans_collection.find.return_value = [
        {
            "_id": "123",
            "username": "test@example.com",
            "content": "Test content",
            "locked": True,
            "created": 0,
            "duration": 1
        }
    ]
    check_and_send_reminders()
    mock_plans_collection.update_one.assert_called_with(
        {"_id": "123"},
        {"$set": {"locked": False}}
    )
