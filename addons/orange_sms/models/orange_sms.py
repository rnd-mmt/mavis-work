import logging
import threading

from odoo import api, fields, models, tools, _
import requests
import json
import re

AUTH_TOKEN_URL = 'https://api.orange.com/oauth/v3/token'

class SMS:
    def __init__(self, auth_token, senderName, clientID, clientSecret):
        """
        auth_token: str-> required.
            This is the Authorization header you will copy from orage developer console.
            It should be of the form "Basic XXXXXXXXXX..."
        """

        if not str(auth_token).startswith('Basic '):
            raise Exception(f"Invalid auth_token: auth_token == '{auth_token}' must start with 'Basic '")
        if senderName is None or len(senderName) == 0:
            raise Exception(f"Invalid senderName. senderName must be a non empty string.")
        self.auth_token = auth_token
        self.senderName = senderName
        self.client_id = clientID
        self.client_secret = clientSecret

    def get_access_token(self):
        """
        It is a good idea to always save the access keys since they are valid for 1 hour.
        You could also set up something like a cloud function that runs every hour to update the access_keys and just read it from database.
        """
        # AUTH API SMS AROVY à mettre dans front dans le futur
        # client_id = 'zQPu6tuEPOJmRuPAJ0UUoc8vYhGK1XE4'
        # client_secret = 'qTyZmzoHOJuxvDRJ'

        client_id = self.client_id
        client_secret = self.client_secret

        headers = {
            "Authorization": self.auth_token,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        data = {"grant_type": "client_credentials"}
        r = requests.post(AUTH_TOKEN_URL, data=data, auth=(client_id, client_secret))
        return r.json().get('access_token')
        # r = requests.post(AUTH_TOKEN_URL, headers=headers, data=data)
        # if r.status_code == 200:
        #     return r.json()['access_token']
        # raise Exception(f"Failed with following response: '{r.text}'")

    def send_sms(self, dev_phone_number, recipient_phone_number, message):
        """
        All parameters are required
        params:
            dev_phone_number: This is the developer's phone number which was used when activating sms.
                Must be formatted as an international phone number beginning matching '[1-9][\d]{10,14}'
            recipient_phone_number: str -> required
                This is the phone number you want to sms to.
                Must be formatted as an international phone number beginning matching '[1-9][\d]{10,14}'
            message: str -> required
                This is the sms message to be sent to the recipient_phone_number by dev_phone_number.
        return: class `requests.Response`
            You must handle the response to see if the message was sent or not.
        """
        # if not re.match('^[1-9][\d]{10,14}$', dev_phone_number):
        #     raise Exception(f"Invalid formate of dev_phone_number. {dev_phone_number} must match regex" + " '[1-9][\d]{10,14}'")
        # if not re.match('^[1-9][\d]{10,14}$', recipient_phone_number):
        #     raise Exception(f"Invalid formate of recipient_phone_number. {recipient_phone_number} must match regex" + " '[1-9][\d]{10,14}'")
        if message is None or len(str(message)) == 0:
            raise Exception("Invalid sms message to send. You must provide a non empty string.")
        send_sms_url = f"https://api.orange.com/smsmessaging/v1/outbound/tel%3A%2B{dev_phone_number}/requests"
        access_token = self.get_access_token()
        headers = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
            'Accept': 'application/json',
        }
        data = {
            "outboundSMSMessageRequest": {
                "address": "tel:" + recipient_phone_number,
                "senderAddress": "tel:+" + dev_phone_number,
                "senderName": self.senderName,
                "outboundSMSTextMessage": {"message": message }
            }
        }
        data = json.dumps(data)
        r = requests.post(send_sms_url, headers= headers, data= data)
        return r


class OrangeSMS(models.Model):
    _inherit = 'sms.sms'

    error_message = fields.Text('Error Message', copy=False, readonly=1)

    def send(self, delete_all=False, auto_commit=False, raise_exception=False):
        """ Main API method to send SMS.

          :param delete_all: delete all SMS (sent or not); otherwise delete only
            sent SMS;
          :param auto_commit: commit after each batch of SMS;
          :param raise_exception: raise if there is an issue contacting IAP;
        """
        # is_message_overwrite = self.env['ir.config_parameter'].sudo().get_param(
        #     'ql_scheduler_reminder.overrwrite_odoo_sms')

        company_id = self.env.company.id
        company_obj = self.env["res.company"].browse(company_id)
        is_message_overwrite = company_obj.overwrite_odoo_sms

        for batch_ids in self._split_batch():
            if not is_message_overwrite:
                self.browse(batch_ids)._send(delete_all=delete_all, raise_exception=raise_exception)
            else:
                self.browse(batch_ids).send_sms()
            # auto-commit if asked except in testing mode

            if auto_commit is True and not getattr(threading.currentThread(), 'testing', False):
                self._cr.commit()

    def send_sms(self, unlink_failed=False, unlink_sent=True, raise_exception=False):
        # todo: fix send sms option
        # param_obj = self.env['ir.config_parameter']
        # auth_token = param_obj.sudo().get_param('ql_scheduler_reminder.auth_token')
        # senderName = param_obj.sudo().get_param('ql_scheduler_reminder.senderName')
        # from_number = param_obj.sudo().get_param('ql_scheduler_reminder.dev_phone_number')
        company_id = self.env.company.id
        param_obj = self.env["res.company"].browse(company_id)
        auth_token = param_obj.auth_token
        senderName = param_obj.senderName
        from_number = param_obj.dev_phone_number
        clientID = param_obj.client_id
        clientSecret = param_obj.client_secret

        for rec_id in self:
            # phone = rec_id.partner_id.phone if rec_id.partner_id else rec_id.number
            phone = rec_id.number
            message = rec_id.body
            try:
                sms = SMS(auth_token=auth_token, senderName=senderName, clientID=clientID, clientSecret=clientSecret)
                res = sms.send_sms(
                    message=message,
                    dev_phone_number=from_number,
                    recipient_phone_number=phone
                )
                print(res)
                if res.status_code == 201:
                    state = 'sent'
                    error_message = None
                else:
                    state = 'error'
                    error_message = res.error_message
            except Exception as e:
                state = 'error'
                error_message = e
            rec_id.write({'error_message': error_message, 'state': state})