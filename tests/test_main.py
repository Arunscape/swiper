import pytest
from swiper.main import ApiClient, Swiper
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)

@pytest.fixture(autouse=True)
def mocked_recs(mocker):
    j = None
    with open("tests/testdata/recs.json") as f:
        j = json.load(f)
    mocker.patch.object(ApiClient, "get_recs", return_value=j)
    mocker.patch.object(ApiClient, "like", return_value=None)
    mocker.patch.object(ApiClient, "dislike", return_value=None)


# @pytest.fixture(scope="session", autouse=True)
# def setup():
#     print("setup")
#     yield
#     print("teardown")


def test_filters():
    a = ApiClient("")
    x = a.get_recs()
    b = a.recs_to_users(x)
    for u in b:
        print(u.bio(), u.check_bio(["vaxx"]))
        # print(u.intent(), u.check_intent(["new friends"]))
        # print(u.interests(), u.check_interests(["cat lover"]))
        print(u.job_titles(), u.check_job(["dog"]))
        # print(u.lifestyles(), u.check_lifestyle(["dog"]))
        # print(u.music_artists(), u.check_music(["the weeknd", "eminem"]))
        # print(u.id(), u.s_number())
        # print(u.photos())

def test_like(caplog):
    caplog.set_level(logging.INFO)
    a = ApiClient("")
    x = a.get_recs()
    b = a.recs_to_users(x)
    b = b[0]
    a.like(b.id(), b.s_number())
    a.dislike(b.id(), b.s_number())
    

def test_swipe():
    s = Swiper("token")
    s.swipe()