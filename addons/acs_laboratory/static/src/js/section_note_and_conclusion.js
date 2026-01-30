odoo.define(
    "acs_laboratory.section_note_and_conclusion_backend",
    function (require) {
      // The goal of this file is to contain JS hacks related to allowing
      // section and note on sale order and invoice.
      console.log(
        "section_and_note_backendsection_and_note_backendsection_and_note_backendsection_and_note_backend"
      );
      ("use strict");
      var FieldChar = require("web.basic_fields").FieldChar;
      var FieldOne2Many = require("web.relational_fields").FieldOne2Many;
      var fieldRegistry = require("web.field_registry");
      var ListFieldText = require("web.basic_fields").ListFieldText;
      var ListRenderer = require("web.ListRenderer");
      console.log(
        "section_and_note_backendsection_and_note_backendsection_and_note_backendsection_and_note_backend"
      );

      // Icône livrer partiellement
    ListRenderer.include({
      _renderHeader: function (isGrouped) {
          const $header = this._super.apply(this, arguments);
          if (this.state.model !== 'patient.laboratory.test') {
              return $header;
          }
          const $iconHeaderCell = $('<th>', {class: 'o_list_icon_header'});
          //$header.find('tr').prepend($iconHeaderCell);
          $header.find('th.o_list_record_selector').after($iconHeaderCell);
          return $header;
      },

      _renderRow: function (record) {
          const $row = this._super.apply(this, arguments);
          const booleanFieldValue = record.data.is_ready_for_partial_delivery;
          const $iconCell = $('<td>', {class: 'o_list_icon_column'});
          if (this.state.model !== 'patient.laboratory.test') {
              return $row;
          }
          if (booleanFieldValue){
              $iconCell.append($('<i>', {class: 'fa fa-adjust', style: 'font-size: 1.5em; position: relative; top: 2px;'}));
          }
          //$row.prepend($iconCell);
          $row.find('td.o_list_record_selector').after($iconCell);
          return $row;
      },
  });

      var ListController = require('web.ListController');
      var core = require('web.core');
      var QWeb = core.qweb;
      ListController.include({
          _onSelectionChanged: function(ev){
              this._super(...arguments);
              if (this.modelName !== 'patient.laboratory.test') return;
              const selectedRecords = this.getSelectedRecords();
              if (!selectedRecords || selectedRecords.length === 0) {
                  return;
              }
              let showButton = false, hideButton = false;
              for (const { data } of selectedRecords) {
                  if (data) {
                      if (data.is_ready_for_partial_delivery === false) showButton = true;
                      if (data.is_ready_for_partial_delivery === true) hideButton = true;
                  }
                  if (showButton && hideButton) break;
              }
              this.$el.find('button[name="set_ready_for_partial_delivery_tree"]').toggle(showButton && !hideButton);
              this.$el.find('button[name="unset_ready_for_partial_delivery_tree"]').toggle(hideButton && !showButton);
          },
      });

  
      var SectionAndNoteListRenderer = ListRenderer.extend({
        /**
         * We want section, note, and conclusion to take the whole line (except handle and trash)
         * to look better and to hide the unnecessary fields.
         *
         * @override
         */
        _renderBodyCell: function (record, node, index, options) {
          var $cell = this._super.apply(this, arguments);
  
          var isSection = record.data.display_type === "line_section";
          var isNote = record.data.display_type === "line_note";
          var isConclusion = record.data.display_type === "line_conclusion"; // New conclusion type
  
          if (isSection || isNote || isConclusion) {
            if (node.attrs.widget === "handle") {
              return $cell;
            } else if (node.attrs.name === "name") {
              var nbrColumns = this._getNumberOfCols();
              if (this.handleField) {
                nbrColumns--;
              }
              if (this.addTrashIcon) {
                nbrColumns--;
              }
              $cell.attr("colspan", nbrColumns);
            } else {
              $cell.removeClass("o_invisible_modifier");
              return $cell.addClass("o_hidden");
            }
          }
  
          return $cell;
        },
        /**
         * We add the o_is_{display_type} class to allow custom behaviour both in JS and CSS.
         *
         * @override
         */
        _renderRow: function (record, index) {
          var $row = this._super.apply(this, arguments);
  
          if (record.data.display_type) {
            if (record.data.display_type === "line_conclusion") {
              $row.addClass("o_is_line_note o_is_line_conlusion");
            } else {
              $row.addClass("o_is_" + record.data.display_type);
            }
          }
  
          return $row;
        },
        /**
         * We want to add .o_section_and_note_list_view on the table to have stronger CSS.
         *
         * @override
         * @private
         */
        _renderView: function () {
          var self = this;
          return this._super.apply(this, arguments).then(function () {
            self.$(".o_list_table").addClass("o_section_and_note_list_view");
          });
        },
      });
  
      // We create a custom widget for the one2many field.
      var SectionAndNoteFieldOne2Many = FieldOne2Many.extend({
        /**
         * We want to use our custom renderer for the list.
         *
         * @override
         */
        _getRenderer: function () {
          if (this.view.arch.tag === "tree") {
            return SectionAndNoteListRenderer;
          }
          return this._super.apply(this, arguments);
        },
      });
  
      // This function determines which field type to use for section and conclusion.
      var SectionAndNoteFieldText = function (parent, name, record, options) {
        var isSection = record.data.display_type === "line_section";
        var isConclusion = record.data.display_type === "line_conclusion"; // New conclusion type
        var Constructor = isSection ? FieldChar : ListFieldText;
        return new Constructor(parent, name, record, options);
      };
  
      fieldRegistry.add(
        "section_note_conclusion_one2many",
        SectionAndNoteFieldOne2Many
      );
      fieldRegistry.add("section_and_note_text", SectionAndNoteFieldText);
  
      return SectionAndNoteListRenderer;
    }
  );
  