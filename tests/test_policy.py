"""Synthetic-only, zero-network tests for the exact reviewed LLM contract."""
import copy
import unittest
from unittest import mock
from llm_mcp import policy as p

CODE = 'def is_even(n: int) -> bool:\n    return n % 2 == 1\n'


def sample(content='Line 2 returns true for odd integers. Change == 1 to == 0.'):
    return {
        'model': 'glm-5.3-flash',
        'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': content}}],
        'usage': {'prompt_tokens': 154, 'completion_tokens': 85},
    }


class ReviewContractTest(unittest.TestCase):
    def test_exact_public_consent_and_digest(self):
        parsed=p.checked_public_python(code=CODE,source_label='synthetic/bug.py',classification='public',consent=True)
        self.assertEqual(parsed['source'],'synthetic/bug.py')
        self.assertEqual(len(parsed['sha256']),64)
        for cls,consent in [('private',True),('public',False),('public','true'),('internal',True)]:
            with self.subTest(cls=cls,consent=consent), self.assertRaises(p.ReviewPolicyError):
                p.checked_public_python(code=CODE,source_label='synthetic/bug.py',classification=cls,consent=consent)

    def test_source_label_and_size_gate(self):
        for label in ['../etc/secrets','/etc/secret','bad name','x','a/../../s']:
            with self.subTest(label=label),self.assertRaises(p.ReviewPolicyError):
                p.checked_public_python(code=CODE,source_label=label,classification='public',consent=True)
        for code in ['abc','def invalid(:\n    pass',CODE+'#'*2500,CODE+'\0']:
            with self.subTest(example=code[:30]),self.assertRaises(p.ReviewPolicyError):
                p.checked_public_python(code=code,source_label='example.py',classification='public',consent=True)
        with self.assertRaises(p.ReviewPolicyError):
            p.checked_public_python(code='def a():\n    return 1\n'+'#hi\n'*75,source_label='example.py',classification='public',consent=True)

    def test_secret_like_source_rejected(self):
        for secret in ['sk-'+'a'*32,'github_pat_'+'x'*24,'rnd_'+'x'*24,'ghp_'+'x'*24]:
            with self.subTest(kind=secret[:4]),self.assertRaises(p.ReviewPolicyError):
                p.checked_public_python(code=f'def token():\n    return {secret!r}\n',source_label='public/example.py',classification='public',consent=True)

    def test_one_exact_model_no_tools_no_fallback(self):
        obj=p.make_payload(code=CODE,source='synthetic/bug.py')
        self.assertEqual(obj['model'],'opencode-go/glm-5.3-flash')
        self.assertEqual(obj['max_tokens'],320)
        self.assertFalse(obj['stream'])
        self.assertNotIn('tools',obj)
        self.assertNotIn('provider',obj)
        self.assertIn('2:     return n % 2',obj['messages'][1]['content'])
        self.assertIn('no tools',obj['messages'][0]['content'].lower())

    def test_model_reply_with_usage_returns_untrusted_content(self):
        parsed=p.parse_upstream_reply(sample())
        self.assertEqual((parsed['input_tokens'],parsed['output_tokens']),(154,85))
        self.assertIn('Line 2',parsed['review'])

    def test_unsafe_response_fails_closed(self):
        cases=[]
        msg=sample();msg['model']='not-allowed';cases.append(msg)
        msg=sample();msg['choices'][0]['message']['tool_calls']=[{'name':'shell'}];cases.append(msg)
        msg=sample();msg['choices'][0]['finish_reason']='length';cases.append(msg)
        msg=sample();msg['usage']['prompt_tokens']=2000;cases.append(msg)
        msg=sample();msg['usage']['completion_tokens']=350;cases.append(msg)
        msg=sample();msg['usage']['completion_tokens']=True;cases.append(msg)
        msg=sample();msg['choices'][0]['message']['content']='Secret key rnd_'+'a'*35;cases.append(msg)
        for item in cases:
            with self.subTest(item=str(item)[:65]),self.assertRaises(p.ReviewPolicyError):
                p.parse_upstream_reply(item)
        with self.assertRaises(p.ReviewPolicyError):
            p.parse_upstream_reply(sample('contains synthetic-access-token'),protected_values=('synthetic-access-token',))

    def test_no_unlimited_parallel_or_budget(self):
        quota=p.LocalReviewQuota(max_calls=2)
        quota.begin()
        with self.assertRaises(p.ReviewPolicyError):quota.begin()
        quota.finish()
        quota.begin();quota.finish()
        with self.assertRaises(p.ReviewPolicyError):quota.begin()

    def test_model_destination_pinned(self):
        self.assertEqual(p.GATEWAY_URL,'https://truthrail-llm-gateway.onrender.com/v1/chat/completions')
        self.assertEqual(p.MODEL,'opencode-go/glm-5.3-flash')

if __name__=='__main__':unittest.main()
