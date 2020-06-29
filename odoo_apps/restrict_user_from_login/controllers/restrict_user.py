# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import Home, Session


class restrict_user(Home):

    @http.route('/web/login', type='http', auth="none", sitemap=False, csrf=False)
    def web_login(self, redirect=None, **kw):
        response = super(restrict_user, self).web_login(redirect, **kw)
        values = request.params.copy()
        if request.params['login_success']:
            uid = request.session.authenticate(
                request.session.db, request.params['login'], request.params['password'])
            user_id = request.env['res.users'].sudo().search(
                [('id', '=', uid)])
            if not user_id.is_login:
                user_id.is_login = True
                return response
            else:
                request.params['login_success'] = False
                values['error'] = _(
                    "You can't Login, Because you are already login from another resourse...")
                request.session.logout(keep_db=True)
                request.uid = request.env.ref('base.public_user').id
                response = request.render('web.login', values)
        return response


class logout_user(Session):

    @http.route('/web/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        uid, login = request.session['uid'], request.session['login']
        user_id = request.env['res.users'].sudo().search(
            [('id', '=', uid), ('active', '=', True), ('login', '=', login)])
        if user_id.is_login:
            user_id.is_login = False
        return super(logout_user, self).logout(redirect)
