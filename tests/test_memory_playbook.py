"""Publishing and retrieving the team skill, with the Playbook SDK replaced by a mock."""
import base64
import io
import json
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


def test_the_best_fitting_team_skill_is_retrieved_and_attendees_cannot_publish(tmp_path):
    client = Mock()
    client.search_skills.return_value = NS(items=[NS(entry_id='ent_logging', version=4, score=0.9), NS(entry_id='ent_team', version=2, score=0.8)])
    client.get_skill_version.return_value = version_content('Never log account numbers.')
    store = PlaybookStore(client, tmp_path / 'publication.json', skill_id='ent_team')
    skill = store.retrieve('add logging to the payment handler', min_score=0.7)
    assert (skill.version, skill.instructions) == (4, 'Never log account numbers.')
    client.get_skill_version.assert_called_once_with(skill_id='ent_logging', version=4)
    with pytest.raises(ValueError, match='instructor'):
        store.publish(skill_folder(tmp_path))


def test_unrelated_task_gets_no_team_skill(tmp_path):
    client = Mock()
    client.search_skills.return_value = NS(items=[NS(entry_id='ent_team', version=1, score=0.55)])
    assert PlaybookStore(client, tmp_path / 'p.json').retrieve('write a haiku', min_score=0.7) is None


def test_retrieval_needs_no_skill_id(tmp_path):
    client = Mock()
    client.search_skills.return_value = NS(items=[NS(entry_id='ent_team', version=1, score=0.9)])
    client.get_skill_version.return_value = version_content('Use Decimal for amounts.')
    assert PlaybookStore(client, tmp_path / 'p.json').retrieve('validate report rows').version == 1


def test_a_skill_below_the_relevance_threshold_is_not_used(tmp_path):
    client = Mock()
    client.search_skills.return_value = NS(items=[NS(entry_id='ent_team', version=3, score=0.57)])
    store = PlaybookStore(client, tmp_path / 'p.json', skill_id='ent_team')
    assert store.retrieve('write a fizzbuzz function', min_score=0.7) is None
    client.get_skill_version.return_value = version_content('Use Decimal for amounts.')
    assert store.retrieve('write a fizzbuzz function') is not None


def test_approved_answers_that_fit_the_task_are_returned(tmp_path):
    client = Mock()
    client.search_faqs.return_value = NS(items=[
        NS(version=2, score=0.91, faq=NS(question='Can I use real customer data in test fixtures?', answer='No. Use synthetic data.')),
        NS(version=1, score=0.66, faq=NS(question='Why does one order have several tracking numbers?', answer='It ships in parts.')),
    ])
    store = PlaybookStore(client, tmp_path / 'p.json', skill_id='ent_team')
    answers = store.answers('Can I put customer data in my fixtures?', min_score=0.75)
    assert [(a.question, a.answer, a.version) for a in answers] == [
        ('Can I use real customer data in test fixtures?', 'No. Use synthetic data.', 2)]
    assert client.search_faqs.call_args.kwargs['query'] == 'Can I put customer data in my fixtures?'


def test_published_skills_are_listed_with_their_versions(tmp_path):
    client = Mock()
    client.list_skills.return_value = NS(items=[
        NS(entry_id='ent_a', publication=NS(version=2)), NS(entry_id='ent_draft', publication=None)])
    client.get_skill_version.return_value = version_content('Use Decimal for amounts.')
    skills = PlaybookStore(client, tmp_path / 'p.json').published_skills()
    assert [(s.name, s.version) for s in skills] == [('report-validation', 2)]
    client.get_skill_version.assert_called_once_with(skill_id='ent_a', version=2)


def test_publishing_a_new_version_keeps_what_else_the_receipt_records(tmp_path):
    client = Mock()
    client.append_skill_version.return_value = NS(entry=NS(entry_id='ent_team'), version=NS(version=2))
    receipt = tmp_path / 'publication.json'
    receipt.write_text('{"entry_id": "ent_team", "version": 1, "digest": "old", "playbook_id": "pb_workshop"}')
    PlaybookStore(client, receipt).publish(skill_folder(tmp_path, 'Validate report rows, version 2'))
    saved = json.loads(receipt.read_text())
    assert (saved['version'], saved['playbook_id']) == (2, 'pb_workshop')


def test_empty_published_content_uses_real_sdk_response_models(tmp_path):
    from redis_agent_playbook.models import (
        ListSkillsResponseContent, SearchSkillsResponseContent, SearchFaqsResponseContent,
    )
    client = Mock()
    client.list_skills.return_value = ListSkillsResponseContent(items=[])
    client.search_skills.return_value = SearchSkillsResponseContent(items=[])
    client.search_faqs.return_value = SearchFaqsResponseContent(items=[])
    store = PlaybookStore(client, tmp_path / 'publication.json')
    assert store.published_skills() == []
    assert store.retrieve('report validation', min_score=0.7) is None
    assert store.answers('API key storage', min_score=0.75) == []
