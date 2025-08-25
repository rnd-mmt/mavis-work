group = env.ref('sales_team.group_sale_manager')
users = group.users
partner_ids = [user.partner_id.id for user in users if user.partner_id]
# Générer l'URL de l'enregistrement
base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
record_url = "%s/web#id=%s&model=sale.order&view_type=form" % (base_url, record.id)
# Envoyer une notification dans le chatter
if partner_ids:
    record.message_post(
        body="Nouvelle commande de vente <b>%s</b> créée et en attente de validation. Accédez à la commande ici : %s" % (record.name, record_url),
        partner_ids=partner_ids,
        subtype_id=env.ref('mail.mt_note').id,
        subject="Nouvelle commande en attente de validation: %s" % record.name,
        author_id=env.ref('base.user_root').id  # Forcer l'auteur à OdooBot
    )