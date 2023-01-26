import pytest
from swiper.main import ApiClient
import json


@pytest.fixture(autouse=True)
def mocked_recs(mocker):
    j = None
    with open("tests/testdata/recs.json") as f:
        j = json.load(f)
    mocker.patch.object(ApiClient, "get_recs", return_value=j)


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
        # print(u.bio(), u.check_bio(["vaxx"]))
        # print(u.intent(), u.check_intent(["new friends"]))
        # print(u.interests(), u.check_interests(["cat lover"]))
        # print(u.job_titles(), u.check_job(["dog"]))
        # print(u.lifestyles(), u.check_lifestyle(["dog"]))
        # print(u.music_artists(), u.check_music(["the weeknd", "eminem"]))
        # print(u.id(), u.s_number())
        print(u.photos())

def test_like():
    a = ApiClient("")
    x = a.get_recs()
    b = a.recs_to_users(x)
    a.like(b.id(), b.s_number())