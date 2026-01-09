"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
from urllib.parse import urlencode

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store the original activities
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Reset activities after test
    for name in activities:
        activities[name]["participants"] = original_activities[name]["participants"].copy()


def test_root_redirect(client):
    """Test that root redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/static/index.html" in response.headers["location"]


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check that activities are returned
    assert isinstance(data, dict)
    assert len(data) > 0
    
    # Check structure of an activity
    assert "Chess Club" in data
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_for_activity_success(client, reset_activities):
    """Test successfully signing up for an activity"""
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}",
        follow_redirects=False
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    
    # Verify the student was added
    assert email in activities[activity_name]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu",
        follow_redirects=False
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_signup_already_registered(client, reset_activities):
    """Test that a student cannot sign up twice for the same activity"""
    activity_name = "Chess Club"
    # michael@mergington.edu is already in Chess Club
    email = "michael@mergington.edu"
    
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}",
        follow_redirects=False
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "already signed up" in data["detail"]


def test_signup_multiple_activities(client, reset_activities):
    """Test that a student can sign up for multiple activities"""
    email = "testuser@mergington.edu"
    
    # Sign up for Chess Club
    response1 = client.post(
        f"/activities/Chess%20Club/signup?email={email}"
    )
    assert response1.status_code == 200
    
    # Sign up for Programming Class
    response2 = client.post(
        f"/activities/Programming%20Class/signup?email={email}"
    )
    assert response2.status_code == 200
    
    # Verify both signups were successful
    assert email in activities["Chess Club"]["participants"]
    assert email in activities["Programming Class"]["participants"]


def test_get_activities_returns_correct_participant_count(client):
    """Test that activities return correct participant counts"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check that participant counts are reasonable
    for activity_name, activity_data in data.items():
        participants_count = len(activity_data["participants"])
        max_participants = activity_data["max_participants"]
        
        assert participants_count <= max_participants
        assert participants_count >= 0


def test_activity_has_available_spots(client, reset_activities):
    """Test that we can see which activities have available spots"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    
    # Find an activity with available spots
    available_activity = None
    for activity_name, activity_data in data.items():
        spots_available = activity_data["max_participants"] - len(activity_data["participants"])
        if spots_available > 0:
            available_activity = activity_name
            break
    
    assert available_activity is not None


def test_signup_with_special_characters_in_email(client, reset_activities):
    """Test signing up with an email that has special characters"""
    activity_name = "Chess Club"
    email = "student+test@mergington.edu"
    
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]


def test_unregister_from_activity_success(client, reset_activities):
    """Test successfully unregistering from an activity"""
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already registered
    
    # Verify participant is initially registered
    assert email in activities[activity_name]["participants"]
    
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    
    # Verify the student was removed
    assert email not in activities[activity_name]["participants"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregistering from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent%20Activity/unregister",
        params={"email": "test@mergington.edu"}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_unregister_not_registered_student(client):
    """Test that unregistering a student who is not registered fails"""
    activity_name = "Chess Club"
    email = "notregistered@mergington.edu"
    
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "not registered" in data["detail"]
