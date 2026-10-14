"""Offline release gates: activation, password hygiene, logout, session expiry."""
import contextlib
import hashlib
import io
import json
import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error
import aiindeksi_bot as app

class ReleaseSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.patch=patch.multiple(app, HERE=self.tmp.name, DB_PATH=os.path.join(self.tmp.name,'db.json'), GH_TOKEN='', TOKEN='', ADMIN_IDS={77001})
        self.patch.start()
        self.db=app._bo_sh_db();self.db['site_accounts_initialized']=True
        self.server=app.make_server(lambda:self.db,port=0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.patch.stop();self.tmp.cleanup()
        app._SITE_AUTH_FAILURES.clear()
    def call(self,path,body=None,token=None):
        headers={'Content-Type':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        request=urllib.request.Request('http://127.0.0.1:%s%s'%(self.server.server_address[1],path),headers=headers,data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(request,timeout=5) as r:return r.status,json.loads(r.read())
        except urllib.error.HTTPError as e:
            try:data=json.loads(e.read())
            except Exception:data={}
            return e.code,data
    def issue(self,login='new-member',mode='member'):
        ok,link=app._site_issue_activation(self.db,login,'telegram:77001',mode)
        self.assertTrue(ok,link)
        return link.split('#token=',1)[1]
    def test_activation_once_and_no_plaintext_in_persisted_db(self):
        token=self.issue();password='Local-only-password-123'
        self.assertNotIn(token,json.dumps(self.db))
        self.assertEqual(self.call('/api/activate',{'token':token,'password':password})[0],200)
        self.assertEqual(self.call('/api/activate',{'token':token,'password':password})[0],400)
        self.assertNotIn(password,open(app.DB_PATH).read())
        self.assertNotIn(token,open(app.DB_PATH).read())
        self.assertEqual(self.call('/api/auth',{'login':'new-member','password':password})[0],200)
    def test_expired_and_tampered_invites_fail(self):
        token=self.issue()
        self.assertFalse(app._site_activate(self.db,token+'tampered','Local-only-password-123')[0])
        with patch.object(app.time,'time',return_value=time.time()+app.SITE_ACTIVATION_TTL+1):
            self.assertFalse(app._site_activate(self.db,token,'Local-only-password-123')[0])
    def test_activation_is_atomic(self):
        token=self.issue();results=[]
        threads=[threading.Thread(target=lambda:results.append(app._site_activate(self.db,token,'Local-only-password-123')[0])) for _ in range(2)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(sorted(results),[False,True])
    def test_reset_disables_old_password_sessions_and_previous_invite(self):
        app._site_create_account(self.db,'test-member','Old-local-password-123','test')
        user=self.db['site_users']['test-member'];old=app._site_issue_session('test-member',user)
        first=self.issue('test-member','reset');second=self.issue('test-member','reset')
        self.assertIsNone(app._site_session_user('Bearer '+old,self.db))
        self.assertFalse(app._site_activate(self.db,first,'New-local-password-123')[0])
        self.assertEqual(self.call('/api/auth',{'login':'test-member','password':'Old-local-password-123'})[0],401)
        self.assertTrue(app._site_activate(self.db,second,'New-local-password-123')[0])
    def test_logout_revokes_all_current_sessions(self):
        app._site_create_account(self.db,'test-member','Local-only-password-123','test')
        token=app._site_issue_session('test-member',self.db['site_users']['test-member'])
        self.assertEqual(self.call('/api/me',token=token)[0],200)
        self.assertEqual(self.call('/api/logout',{},token)[0],200)
        self.assertEqual(self.call('/api/me',token=token)[0],401)
    def test_password_commands_are_rejected_and_not_saved(self):
        msg={'chat':{'id':77001,'type':'private'},'message_id':1,'text':'/qosh test-member Never-send-this-password'}
        reply,_=app._site_account_bot_command(msg,self.db,msg['text'])
        self.assertIn('Parolni Telegramga yozmang',reply)
        self.assertNotIn('test-member',self.db['site_users'])
        self.assertNotIn('Never-send-this-password',reply+json.dumps(self.db))
    def test_group_password_message_deletion_is_attempted_without_provisioning(self):
        msg={'chat':{'id':-10077001,'type':'supergroup'},'from':{'id':77001},'message_id':1,'text':'/qosh test-member Never-send-this-password'}
        with patch.object(app,'tg',return_value=True) as tg:
            app.update_ishla({'message':msg},self.db)
            tg.assert_called_once_with('deleteMessage',chat_id=-10077001,message_id=1)
        self.assertNotIn('test-member',self.db['site_users'])
    def test_non_admin_cannot_issue_invite(self):
        msg={'chat':{'id':77002,'type':'private'},'text':'/sayt_admin malicious'}
        reply,_=app._site_account_bot_command(msg,self.db,msg['text'])
        self.assertIn("Bunday buyruq yo'q",reply)
        self.assertNotIn('malicious',self.db['site_users'])
    def test_admin_invite_preserves_role_after_activation(self):
        token=self.issue('new-admin','admin')
        self.assertTrue(app._site_activate(self.db,token,'Admin-local-password-123')[0])
        self.assertTrue(self.db['site_users']['new-admin']['is_admin'])
    def test_release_health_reports_auth_api_version(self):
        status,data=self.call('/healthz')
        self.assertEqual(status,200);self.assertEqual(data['auth_api'],2)
        self.assertEqual(data['release'],'2026-10-14.1')

if __name__=='__main__': unittest.main()
