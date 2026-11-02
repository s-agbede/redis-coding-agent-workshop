import base64
import io
from types import SimpleNamespace as NS
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
pytest.importorskip('redis_agent_playbook')


def test_package_has_root_skill_folder_and_rejects_symlinks(tmp_path):
    from playbook import encode_package
    folder = tmp_path / 'report-validation'; folder.mkdir()
    (folder / 'SKILL.md').write_text('Instructions')
    with ZipFile(io.BytesIO(base64.b64decode(encode_package(folder)))) as archive:
        assert archive.namelist() == ['report-validation/SKILL.md']
    (folder / 'secret').symlink_to(tmp_path / 'outside')
    with pytest.raises(ValueError, match='symlink'):
        encode_package(folder)


def test_retrieval_uses_search_version_and_ignores_unrelated_entries(tmp_path):
    from playbook import PlaybookStore, Receipt
    client=Mock()
    store=PlaybookStore(client,'pb_test',tmp_path/'receipt.json','owner')
    store.save(Receipt(playbook_id='pb_test',owner='owner',entry_id='ent_own',version=2,package_digest='abc'))
    client.search_skills.return_value=NS(matches=[NS(entry_id='ent_other',version=9),NS(entry_id='ent_own',version=2)])
    client.get_skill.return_value=NS(publication=NS(version=2))
    client.get_skill_version.return_value=NS(entry_id='ent_own',version=2,content_digest='digest',content=NS(payload=NS(skill=NS(instructions='Check IDs',resources=[]))))
    result=store.retrieve('validate report')
    assert result.version==2 and result.instructions=='Check IDs'
    client.get_skill_version.assert_called_once_with(skill_id='ent_own',version=2)
    assert result.source.endswith('/ent_own/versions/2')


def test_empty_search_does_not_substitute_local_skill(tmp_path):
    from playbook import PlaybookStore, Receipt
    client=Mock(); store=PlaybookStore(client,'pb_test',tmp_path/'receipt.json','owner')
    store.save(Receipt(playbook_id='pb_test',owner='owner',entry_id='ent_own',version=1,package_digest='abc'))
    client.search_skills.return_value=NS(matches=[])
    assert store.retrieve('unrelated task') is None
    client.get_skill_version.assert_not_called()


def test_publication_retry_uses_saved_draft_and_confirms_remote_version(tmp_path):
    from playbook import PlaybookStore
    folder = tmp_path/'report-validation'; folder.mkdir()
    (folder/'SKILL.md').write_text('Validate report rows')
    client = Mock()
    store = PlaybookStore(client, 'pb', tmp_path/'receipt.json', 'learner')
    client.create_skill.return_value = NS(entry=NS(entry_id='entry'), version=NS(version=1))
    client.get_skill.return_value = NS(publication=None)
    client.publish_skill.side_effect = RuntimeError('temporarily unavailable')
    with pytest.raises(RuntimeError):
        store.publish(folder)
    assert store.receipt().entry_id == 'entry'
    client.publish_skill.side_effect = None
    client.publish_skill.return_value = NS(publication=NS(version=1))
    assert store.publish(folder).version == 1
    assert client.create_skill.call_count == 1
    client.get_skill.return_value = NS(publication=NS(version=1))
    assert store.publish(folder).version == 1
    assert client.publish_skill.call_count == 2


def test_retrieval_rejects_changed_publication(tmp_path):
    from playbook import PlaybookStore, Receipt
    client = Mock()
    store = PlaybookStore(client, 'pb', tmp_path/'receipt.json', 'learner')
    store.save(Receipt(playbook_id='pb', owner='learner',entry_id='entry',version=1,package_digest='digest'))
    client.search_skills.return_value = NS(matches=[NS(entry_id='entry', version=1)])
    client.get_skill.return_value = NS(publication=NS(version=2))
    with pytest.raises(ValueError, match='changed'):
        store.retrieve('validate rows')
    client.get_skill_version.assert_not_called()


def test_attendee_retrieves_instructor_skill_without_a_receipt(tmp_path):
    from playbook import PlaybookStore
    client = Mock()
    store = PlaybookStore(client, 'pb', tmp_path/'receipt.json', 'attendee', skill_id='ent_team')
    client.search_skills.return_value = NS(matches=[NS(entry_id='ent_stale', version=4), NS(entry_id='ent_team', version=1)])
    client.get_skill.return_value = NS(publication=NS(version=1))
    client.get_skill_version.return_value = NS(entry_id='ent_team', version=1, content_digest='d', content=NS(payload=NS(skill=NS(instructions='Team rules', resources=[]))))
    result = store.retrieve('validate report')
    assert result.instructions == 'Team rules'
    client.get_skill_version.assert_called_once_with(skill_id='ent_team', version=1)


def test_attendee_publish_is_refused_as_an_instructor_step(tmp_path):
    from playbook import PlaybookStore
    folder = tmp_path/'report-validation'; folder.mkdir()
    (folder/'SKILL.md').write_text('Validate report rows')
    client = Mock()
    store = PlaybookStore(client, 'pb', tmp_path/'receipt.json', 'attendee', skill_id='ent_team')
    with pytest.raises(ValueError, match='instructor'):
        store.publish(folder)
    assert not client.mock_calls


def test_retrieval_without_receipt_or_skill_id_names_the_setting(tmp_path):
    from playbook import PlaybookStore
    store = PlaybookStore(Mock(), 'pb', tmp_path/'receipt.json', 'attendee')
    with pytest.raises(ValueError, match='PLAYBOOK_SKILL_ID'):
        store.retrieve('validate report')


def test_changed_skill_publishes_a_new_version_of_the_same_entry(tmp_path):
    from playbook import PlaybookStore, Receipt
    folder = tmp_path/'report-validation'; folder.mkdir()
    (folder/'SKILL.md').write_text('Validate report rows, version two')
    client = Mock()
    store = PlaybookStore(client, 'pb', tmp_path/'receipt.json', 'instructor')
    store.save(Receipt(playbook_id='pb', owner='instructor', entry_id='entry', version=1, package_digest='old'))
    client.append_skill_version.return_value = NS(entry=NS(entry_id='entry'), version=NS(version=2))
    client.get_skill.return_value = NS(publication=NS(version=1))
    client.publish_skill.return_value = NS(publication=NS(version=2))
    receipt = store.publish(folder)
    assert (receipt.entry_id, receipt.version) == ('entry', 2)
    assert store.receipt().version == 2
    client.create_skill.assert_not_called()
    client.publish_skill.assert_called_once_with(skill_id='entry', version=2)
