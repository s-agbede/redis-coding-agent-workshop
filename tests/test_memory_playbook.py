"""Publishing and retrieving the team skill, with the Playbook SDK replaced by a mock."""
import base64
import io
from types import SimpleNamespace as NS
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

pytest.importorskip('redis_agent_playbook')
from playbook import PlaybookStore, encode_package


def skill_folder(tmp_path, text='Validate report rows'):
    folder = tmp_path / 'report-validation'
    folder.mkdir(exist_ok=True)
    (folder / 'SKILL.md').write_text(text)
    return folder


def version_content(instructions):
    return NS(content=NS(payload=NS(skill=NS(manifest=NS(name='report-validation'), instructions=instructions))))


def test_package_is_rooted_at_the_skill_folder(tmp_path):
    with ZipFile(io.BytesIO(base64.b64decode(encode_package(skill_folder(tmp_path))))) as archive:
        assert archive.namelist() == ['report-validation/SKILL.md']


def test_first_publish_creates_and_publishes_and_unchanged_content_is_not_republished(tmp_path):
    client = Mock()
    client.create_skill.return_value = NS(entry=NS(entry_id='ent_team'), version=NS(version=1))
    store = PlaybookStore(client, tmp_path / 'publication.json')
    folder = skill_folder(tmp_path)
    assert store.publish(folder) == ('ent_team', 1)
    client.publish_skill.assert_called_once_with(skill_id='ent_team', version=1)
    assert store.publish(folder) == ('ent_team', 1)
    assert client.create_skill.call_count == 1 and client.publish_skill.call_count == 1


def test_changed_skill_becomes_the_next_version_of_the_same_entry(tmp_path):
    client = Mock()
    client.create_skill.return_value = NS(entry=NS(entry_id='ent_team'), version=NS(version=1))
    client.append_skill_version.return_value = NS(entry=NS(entry_id='ent_team'), version=NS(version=2))
    store = PlaybookStore(client, tmp_path / 'publication.json')
    store.publish(skill_folder(tmp_path))
    assert store.publish(skill_folder(tmp_path, 'Validate report rows. Use Decimal.')) == ('ent_team', 2)
    client.publish_skill.assert_called_with(skill_id='ent_team', version=2)


def test_attendees_retrieve_the_instructor_skill_and_cannot_publish(tmp_path):
    client = Mock()
    client.search_skills.return_value = NS(matches=[NS(entry_id='ent_other', version=4, score=0.9), NS(entry_id='ent_team', version=2, score=0.8)])
    client.get_skill_version.return_value = version_content('Use Decimal for amounts.')
    store = PlaybookStore(client, tmp_path / 'publication.json', skill_id='ent_team')
    skill = store.retrieve('validate report rows')
    assert (skill.name, skill.version, skill.instructions) == ('report-validation', 2, 'Use Decimal for amounts.')
    client.get_skill_version.assert_called_once_with(skill_id='ent_team', version=2)
    with pytest.raises(ValueError, match='instructor'):
        store.publish(skill_folder(tmp_path))


def test_unrelated_task_gets_no_team_skill(tmp_path):
    client = Mock()
    client.search_skills.return_value = NS(matches=[NS(entry_id='ent_other', version=1, score=0.9)])
    assert PlaybookStore(client, tmp_path / 'p.json', skill_id='ent_team').retrieve('write a haiku') is None


def test_retrieval_without_any_skill_names_the_setting(tmp_path):
    with pytest.raises(ValueError, match='PLAYBOOK_SKILL_ID'):
        PlaybookStore(Mock(), tmp_path / 'p.json').retrieve('validate report rows')


def test_a_skill_below_the_relevance_threshold_is_not_used(tmp_path):
    client = Mock()
    client.search_skills.return_value = NS(matches=[NS(entry_id='ent_team', version=3, score=0.57)])
    store = PlaybookStore(client, tmp_path / 'p.json', skill_id='ent_team')
    assert store.retrieve('write a fizzbuzz function', min_score=0.7) is None
    client.get_skill_version.return_value = version_content('Use Decimal for amounts.')
    assert store.retrieve('write a fizzbuzz function') is not None
