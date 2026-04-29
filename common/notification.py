"""
通知模块
支持邮件、钉钉机器人、企业微信机器人、飞书机器人消息发送
通过 config 中对应的 *_CONFIG 控制开关和参数
"""
import hashlib
import hmac
import base64
import time
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import List, Optional, Dict, Any

import requests

import setting as config
from common.logger import logger
from common.console import print_success, print_error


# ==================== 邮件 ====================

class EmailNotifier:
    """邮件通知，配置来源 config.EMAIL_CONFIG"""

    def __init__(self):
        cfg = config.EMAIL_CONFIG
        self._enabled = cfg.get('enabled', False)
        self._smtp_server = cfg.get('smtp_server', '')
        self._smtp_port = cfg.get('smtp_port', 587)
        self._username = cfg.get('smtp_username', '')
        self._password = cfg.get('smtp_password', '')
        self._sender = cfg.get('sender', '')
        self._default_receivers = cfg.get('receivers', [])
        self._subject_prefix = cfg.get('subject_prefix', '[AutoApiTest] ')

    def send(self, subject: str, body: str, to: Optional[List[str]] = None,
             cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None,
             attachments: Optional[List[str]] = None, html: bool = False):
        """
        发送邮件

        Args:
            subject: 邮件主题
            body: 邮件正文
            to: 收件人列表，不传则使用 config 中的默认收件人
            cc: 抄送列表
            bcc: 密送列表
            attachments: 附件路径列表
            html: 正文是否为 HTML 格式
        """
        if not self._enabled:
            logger.debug('邮件通知未启用，跳过发送')
            return

        receivers = to or self._default_receivers
        if isinstance(receivers, str):
            receivers = [receivers]

        msg = MIMEMultipart()
        msg['From'] = self._sender
        msg['To'] = ', '.join(receivers)
        msg['Subject'] = f'{self._subject_prefix}{subject}'

        if cc:
            msg['Cc'] = ', '.join(cc if isinstance(cc, list) else [cc])
            receivers = receivers + (cc if isinstance(cc, list) else [cc])
        if bcc:
            receivers = receivers + (bcc if isinstance(bcc, list) else [bcc])

        subtype = 'html' if html else 'plain'
        msg.attach(MIMEText(body, subtype, 'utf-8'))

        if attachments:
            for filepath in attachments:
                with open(filepath, 'rb') as f:
                    part = MIMEApplication(f.read())
                    part.add_header('Content-Disposition', 'attachment',
                                    filename=Path(filepath).name)
                    msg.attach(part)

        try:
            with smtplib.SMTP(self._smtp_server, self._smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self._username, self._password)
                server.sendmail(self._sender, receivers, msg.as_string())
            logger.info(f'邮件已发送: {subject}')
            print_success(f'邮件已发送到 {len(receivers)} 个收件人')
        except Exception as e:
            logger.error(f'邮件发送失败: {e}')
            print_error(f'邮件发送失败: {e}')


# ==================== 钉钉机器人 ====================

class DingTalkNotifier:
    """钉钉群机器人通知，配置来源 config.DINGTALK_CONFIG"""

    def __init__(self):
        cfg = config.DINGTALK_CONFIG
        self._enabled = cfg.get('enabled', False)
        self._webhook_url = cfg.get('webhook_url', '')
        self._secret = cfg.get('secret', '')
        self._default_at_mobiles = cfg.get('at_mobiles', [])
        self._default_at_all = cfg.get('at_all', False)

    def _sign(self) -> tuple:
        """生成钉钉加签参数 (timestamp, sign)"""
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f'{timestamp}\n{self._secret}'
        sign = base64.b64encode(
            hmac.new(
                self._secret.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        return timestamp, urllib.parse.quote_plus(sign)

    def _get_url(self) -> str:
        url = self._webhook_url
        if self._secret:
            timestamp, sign = self._sign()
            url = f'{url}&timestamp={timestamp}&sign={sign}'
        return url

    def _post(self, payload: dict):
        if not self._enabled:
            logger.debug('钉钉通知未启用，跳过发送')
            return

        try:
            resp = requests.post(self._get_url(), json=payload, timeout=10)
            result = resp.json()
            if result.get('errcode') == 0:
                logger.info('钉钉消息已发送')
                print_success('钉钉消息已发送')
            else:
                logger.error(f'钉钉消息发送失败: {result}')
                print_error(f'钉钉消息发送失败: {result}')
        except Exception as e:
            logger.error(f'钉钉消息发送异常: {e}')
            print_error(f'钉钉消息发送异常: {e}')

    def _build_at(self, at_mobiles: Optional[List[str]], at_all: Optional[bool]) -> dict:
        mobiles = at_mobiles if at_mobiles is not None else self._default_at_mobiles
        all_ = at_all if at_all is not None else self._default_at_all
        if mobiles or all_:
            return {'atMobiles': mobiles or [], 'isAtAll': all_}
        return {}

    def send_text(self, content: str, at_mobiles: Optional[List[str]] = None,
                  at_all: Optional[bool] = None):
        payload: Dict[str, Any] = {
            'msgtype': 'text',
            'text': {'content': content},
        }
        at = self._build_at(at_mobiles, at_all)
        if at:
            payload['at'] = at
        self._post(payload)

    def send_markdown(self, title: str, text: str, at_mobiles: Optional[List[str]] = None,
                      at_all: Optional[bool] = None):
        payload: Dict[str, Any] = {
            'msgtype': 'markdown',
            'markdown': {'title': title, 'text': text},
        }
        at = self._build_at(at_mobiles, at_all)
        if at:
            payload['at'] = at
        self._post(payload)

    def send_link(self, title: str, text: str, message_url: str, pic_url: str = ''):
        payload = {
            'msgtype': 'link',
            'link': {
                'title': title,
                'text': text,
                'messageUrl': message_url,
                'picUrl': pic_url,
            }
        }
        self._post(payload)


# ==================== 企业微信机器人 ====================

class WeComNotifier:
    """企业微信群机器人通知，配置来源 config.WECOM_CONFIG"""

    def __init__(self):
        cfg = config.WECOM_CONFIG
        self._enabled = cfg.get('enabled', False)
        self._webhook_url = cfg.get('webhook_url', '')
        self._default_mentioned_list = cfg.get('mentioned_list', [])
        self._default_mentioned_mobile_list = cfg.get('mentioned_mobile_list', [])

    def _post(self, payload: dict):
        if not self._enabled:
            logger.debug('企业微信通知未启用，跳过发送')
            return

        try:
            resp = requests.post(self._webhook_url, json=payload, timeout=10)
            result = resp.json()
            if result.get('errcode') == 0:
                logger.info('企业微信消息已发送')
                print_success('企业微信消息已发送')
            else:
                logger.error(f'企业微信消息发送失败: {result}')
                print_error(f'企业微信消息发送失败: {result}')
        except Exception as e:
            logger.error(f'企业微信消息发送异常: {e}')
            print_error(f'企业微信消息发送异常: {e}')

    def send_text(self, content: str, mentioned_list: Optional[List[str]] = None,
                  mentioned_mobile_list: Optional[List[str]] = None):
        payload = {
            'msgtype': 'text',
            'text': {
                'content': content,
                'mentioned_list': mentioned_list or self._default_mentioned_list,
                'mentioned_mobile_list': mentioned_mobile_list or self._default_mentioned_mobile_list,
            }
        }
        self._post(payload)

    def send_markdown(self, content: str):
        payload = {
            'msgtype': 'markdown',
            'markdown': {'content': content}
        }
        self._post(payload)


# ==================== 飞书机器人 ====================

class FeishuNotifier:
    """飞书群机器人通知，配置来源 config.FEISHU_CONFIG"""

    def __init__(self):
        cfg = config.FEISHU_CONFIG
        self._enabled = cfg.get('enabled', False)
        self._webhook_url = cfg.get('webhook_url', '')
        self._secret = cfg.get('secret', '')

    def _sign(self) -> tuple:
        """生成飞书签名 (timestamp, sign)"""
        timestamp = str(int(time.time()))
        string_to_sign = f'{timestamp}\n{self._secret}'
        sign = base64.b64encode(
            hmac.new(
                string_to_sign.encode('utf-8'),
                self._secret.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        return timestamp, sign

    def _post(self, payload: dict):
        if not self._enabled:
            logger.debug('飞书通知未启用，跳过发送')
            return

        # 加签参数放入请求体
        if self._secret:
            timestamp, sign = self._sign()
            payload['timestamp'] = timestamp
            payload['sign'] = sign

        try:
            resp = requests.post(self._webhook_url, json=payload, timeout=10)
            result = resp.json()
            if result.get('code') == 0:
                logger.info('飞书消息已发送')
                print_success('飞书消息已发送')
            else:
                logger.error(f'飞书消息发送失败: {result}')
                print_error(f'飞书消息发送失败: {result}')
        except Exception as e:
            logger.error(f'飞书消息发送异常: {e}')
            print_error(f'飞书消息发送异常: {e}')

    def send_text(self, content: str):
        payload = {
            'msg_type': 'text',
            'content': {'text': content},
        }
        self._post(payload)

    def send_post(self, title: str, content: List[List[Dict[str, str]]]):
        """发送富文本消息

        Args:
            title: 消息标题
            content: 富文本内容，格式为 [[{tag, text}, ...], ...]
                     每个内层 list 是一行，每行由多个 tag+text 元素组成
                     支持的 tag: text, a, at
        """
        payload = {
            'msg_type': 'post',
            'content': {
                'post': {
                    'zh_cn': {
                        'title': title,
                        'content': content,
                    }
                }
            }
        }
        self._post(payload)

    def send_interactive(self, title: str, elements: List[dict], header_color: str = 'blue'):
        """发送卡片消息

        Args:
            title: 卡片标题
            elements: 卡片元素列表，每个元素为飞书卡片 JSON 对象
            header_color: 标题颜色 (blue|red|green|yellow|purple|wathet|turquoise)
        """
        payload = {
            'msg_type': 'interactive',
            'card': {
                'header': {
                    'title': {'tag': 'plain_text', 'content': title},
                    'template': header_color,
                },
                'elements': elements,
            }
        }
        self._post(payload)
