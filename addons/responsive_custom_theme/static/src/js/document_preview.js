odoo.define('responsive_custom_theme.document_preview', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');
    var KanbanRecord = require('web.KanbanRecord');
    var rpc = require('web.rpc');
    var DocumentViewer = require("mail.DocumentViewer");

    // Fonction utilitaire pour ouvrir ou télécharger une pièce jointe.
    function openAttachmentPreview(attachmentId, context) {
        if (isNaN(attachmentId)) {
            console.error("Invalid attachment ID: ", attachmentId);
            return;
        }
        // Recherche de la pièce jointe
        rpc.query({
            model: 'ir.attachment',
            method: 'read',
            args: [[attachmentId], ['mimetype', 'name', 'url', 'datas']],
        }).then(function (attachments) {
            if (attachments.length > 0) {
                var attachment = attachments[0];
                var mimetype = attachment.mimetype;

                // Vérifie sy la pièce jointe image, PDF, or plain text
                var isImage = mimetype && mimetype.startsWith('image/');
                var isPDF = mimetype && mimetype === 'application/pdf';
                var isText = mimetype && mimetype === 'text/plain';

                // Faire le toggle du base URL
                function getFullUrl(url) {
                    if (!url) return '';
                    if (url.startsWith('http') || url.startsWith('https')) {
                        return url;
                    }
                    // Si chemin relative, ajouter le base URL
                    return window.location.origin + url;
                }

                // Visualisation image, PDF, and text
                if (isImage || isPDF || isText) {
                    var attachmentUrl = attachment.url || '';
                    var attachmentDatas = attachment.datas || '';

                    // Faire le toggle du base URL
                    attachmentUrl = getFullUrl(attachmentUrl);

                    if (attachmentUrl) {
                        // Visualisation
                        var viewerData = {
                            attachments: [
                                {
                                    id: attachment.id,
                                    name: attachment.name,
                                    type: 'url',
                                    mimetype: attachment.mimetype,
                                    url: attachmentUrl,
                                    datas: '',
                                }
                            ],
                            attachmentID: attachment.id,
                        };

                        // Initialisation du DocumentViewer
                        var viewer = new DocumentViewer(context, viewerData.attachments, viewerData.attachmentID);
                        viewer.appendTo($('body'));
                        viewer.open();
                    } else if (attachmentDatas) {
                        // Si l'URL est une base64
                        var viewerData = {
                            attachments: [
                                {
                                    id: attachment.id,
                                    name: attachment.name,
                                    type: 'binary',
                                    mimetype: attachment.mimetype,
                                    url: '',
                                    datas: attachment.datas,
                                }
                            ],
                            attachmentID: attachment.id,
                        };

                        // Initialisation du Document viewer avec le Base64
                        var viewer = new DocumentViewer(context, viewerData.attachments, viewerData.attachmentID);
                        viewer.appendTo($('body'));
                        viewer.open();
                    } else {
                        console.error("No valid URL or Base64 data for attachment ID: ", attachmentId);
                    }
                } else {
                    // Télécharger le fichier si ce c'est pas une image ou pdf ou texte pleinne
                    downloadAttachment(attachment);
                }
            } else {
                console.error("Pas de pièce jointes avec l' ID: " + attachmentId);
            }
        }).catch(function (error) {
            console.error("Il y a un erreur lors de la recherche de la pièce jointe : ", error);
        });
    }



    // Fonction pour télécharger une pièce jointe
    function downloadAttachment(attachment) {
        var downloadUrl = `/web/content/${attachment.id}?download=true`;
        var a = document.createElement('a');
        a.href = downloadUrl;
        a.download = attachment.name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    // Surcharge de la méthode _onRowClicked pour ListRenderer (List view)
    ListRenderer.include({
        _onRowClicked: function (event) {
            var self = this;
            var $target = $(event.target).closest('tr');
            var attachmentModel = this.state.model;
            var offset = this.state.offset || 0;
            var rowIndex = offset + $target.index();
            var attachmentRecord = this.state.data[rowIndex];
            var attachmentId = attachmentRecord ? attachmentRecord.res_id : null;

            if (attachmentModel === 'ir.attachment' && attachmentId) {
                event.preventDefault();
                event.stopPropagation();
                openAttachmentPreview(attachmentId, self);
            } else {
                this._super.apply(this, arguments);
            }
        }
    });

    // Surcharge de la méthode _onGlobalClick pour KanbanRecord (Kanban view)
    KanbanRecord.include({
        _onGlobalClick: function (event) {
            var self = this;
            var attachmentModel = this.modelName;
            var attachmentId = this.id;

            if (attachmentModel === 'ir.attachment') {
                event.preventDefault();
                event.stopPropagation();
                openAttachmentPreview(attachmentId, self);
            } else {
                this._super.apply(this, arguments);
            }
        }
    });

});
