from odoo import models, fields, api, _

from operator import itemgetter


import logging


_logger = logging.getLogger(__name__)  # Need for message in console.


class ProjectTaskTreeUpdate(models.Model):
    _name = 'project.task'
    _inherit = 'project.task'

    def tree_onfly(self, query, parent):  # array with inside array for sorting only in level.
        parent['children'] = []
        for item in query:
            if item['parent_id'] == parent['id']:
                parent['children'].append(item)
                self.tree_onfly(query, item)
        return parent


    def flat_onfly(self, object, level=0):  # recusive search sub level.
        result = []



        def _get_rec(object, level, parent=None):

            object = sorted(object, key=itemgetter('sorting_seq'))
            for line in object:

                res = {}
                res['id'] = '{}'.format(line["id"])
                res['name'] = u'{}'.format(line["name"])
                res['parent_id'] = u'{}'.format(line["parent_id"])
                res['sorting_seq'] = line["sorting_seq"]
                res['level'] = '{}'.format(level)

                result.append(res)

                if line["children"]:

                    if level < 16:
                        level += 1
                        parent = line["id"]

                    _get_rec(line["children"], level, parent)

                    if level > 0 and level < 16:
                        level -= 1
                        parent = None

            return result



        children = _get_rec(object, level)

        return children


    def do_sorting(self, project_id=None):  # recusive search sub level.

        search_objs = self.sudo().search([('project_id', '=', project_id)], order="sorting_seq asc")

        line_datas = []
        for search_obj in search_objs:
            res = {}
            res['id'] = '{}'.format(search_obj.id)
            res['name'] = u'{}'.format(search_obj.name)
            res['parent_id'] = u'{}'.format(search_obj.parent_id.id)
            res['sorting_seq'] = search_obj.sorting_seq

            line_datas.append(res)

        root = {'id': "False"}

        # Stroim derevo s uchetom vseh pod urovnej.
        tree_onfly = self.tree_onfly(line_datas, root)

        # Razvorachivajem derevo v ploskuju strukturu i sortirujem po Index. Takim obrazom poluchajem
        # otsortirovanoje derevo dla vivoda v proskom rezime na UI.
        flat_onfly = self.flat_onfly(tree_onfly["children"])

        for index, line in enumerate(flat_onfly):
            var_data = {
                "sorting_seq": index + 1,
                "sorting_level": int(line["level"]),
            }

            task_obj = self.env['project.task']
            task_obj_search = task_obj.sudo().search([('id', '=', int(line["id"]))])
            task_obj_search.sudo().write(var_data)





