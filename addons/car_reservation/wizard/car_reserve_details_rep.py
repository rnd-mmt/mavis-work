# See LICENSE file for full copyright and licensing details.
"""Wizard car reserve details export TransientModel."""

import base64
import os
import pytz
import xlsxwriter
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import date_utils, DEFAULT_SERVER_DATE_FORMAT as DF


class WizCarReserveDetailsReport(models.TransientModel):
    """Wizard car reserve details export TransientModel."""

    _name = "wiz.car.reserve.details.export"
    _description = "Wizard Car Reservation Details Export"

    vehicle_ids = fields.Many2many("fleet.vehicle",
                                   "wiz_fleet_vehicle_rel", "wiz_car_res_id",
                                   "vehicle_id", "Vehicles")
    date_from = fields.Datetime(
        string='Date From',
        default=date_utils.start_of(datetime.now(), 'month'))
    date_to = fields.Datetime(
        string='Date To',
        default=date_utils.end_of(datetime.now(), 'month'))

    @api.model
    def default_get(self, fields):
        res = super(WizCarReserveDetailsReport,self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model', [])
        if active_model == "car.reservation" and active_ids:
            recs = self.env[active_model].browse(active_ids).mapped('vehicle_id')
            if recs:
                res['vehicle_ids'] = [(6, 0, recs.ids)]
        return res

    @api.constrains("date_from", "date_to")
    def _constraint_date_limit(self):
        """Method is used to Validate a Date Constraint."""
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise UserError(_("End date must be greater "
                                  "than the start date !"))
        return True

    def print_report(self):
        """Method to Export Car Reservation Details Report."""
        wiz_download_rep_obj = self.env["wiz.download.reserve.report"]
        reservation_recs = False
        vehicle_recs = False
        # sheet Development
        file_path = "Car Reservation Details.xlsx"
        workbook = xlsxwriter.Workbook("/tmp/" + file_path)
        merge_format = workbook.add_format({
            "bold": 1,
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "font": "height 210, name Calibri",
            "fg_color": "#32CD32",
        })

        merge_cell_format = workbook.add_format({
            "font_name": "Arial",
            "font_size": 10,
            "fg_color": "#96c5f4",
            "align": "center",
            "valign": "vcenter",
        })

        dom = [("start_date", ">=", self.date_from),
               ("end_date", "<=", self.date_to)]
        if self.vehicle_ids:
            dom += [("vehicle_id", "in", self.vehicle_ids.ids)]

        reservation_recs = self.env["car.reservation"].search(dom)

        vehicle_recs = reservation_recs.mapped("vehicle_id")

        lang = self.env.user.lang
        lang_recs = self.env['res.lang'].search([("code", "=", lang)], limit=1)
        if lang_recs:
            df = str(lang_recs.date_format)
        else:
            df = DF

        if not reservation_recs:
            raise UserError(_("No Car Reservation records found between "
                              "this duration! "))
        for vehicle_rec in vehicle_recs:
            col = 0
            row = 0
            vehicle_date_dict = {}
            vehicle_time_dict = {}
            # Preparing Sheet name

            vehicle_model = vehicle_rec.model_id
            vehicle_brand = vehicle_model and vehicle_model.brand_id or ""
            brand_name = vehicle_brand and vehicle_brand.name or ""
            sheet_name = (vehicle_model and vehicle_model.name + "-" +
                          vehicle_rec.license_plate)
            worksheet = workbook.add_worksheet(sheet_name)
            row = 1
            # Fetching Min.date and Max.Date.
            self._cr.execute(
                """select min(start_date),max(end_date) from
                    car_reservation where vehicle_id = %s and id in %s""",
                (vehicle_rec.id, tuple(reservation_recs.ids),),
            )
            min_date_res, max_date_res = self._cr.fetchone()
            min_dt = min_date_res
            max_dt = max_date_res
            worksheet.write(row, col, "DATA", merge_format)
            # Dates
            # for printing max date too in sheet we are setting it as max hours
            # minutes/seconds.
            max_dt = max_dt + relativedelta(hour=23, minute=59, second=59)
            # Using while writing date in each row first and storing date with
            # row no.in dictionary having date from min.to max.date
            # .e.g {'2017-08-31': [2]}
            while min_dt <= max_dt:
                row += 1
                disp_dt = datetime.strftime(min_dt, df)
                worksheet.write(row, col, disp_dt)
                vehicle_date_dict[disp_dt] = [row]
                min_dt += relativedelta(days=1)
            # Resetting row and col .cause after writing date pointer in excel
            # needs at first position to write Time in columns.
            row = 1
            col = 1
            tz_name = self._context.get("tz", "UTC")
            self._cr.execute(
                """select start_date
                         as mn from car_reservation cr where vehicle_id = %s
                         and id in %s group by cr.id order by mn limit 1""",
                (vehicle_rec.id, tuple(reservation_recs.ids),),
            )
            min_hr_dt = self._cr.dictfetchone()
            utc_timestamp = pytz.utc.localize(
                min_hr_dt.get("mn"), is_dst=False)
            min_hr_dt = utc_timestamp.astimezone(pytz.timezone(tz_name))
            min_st_hour = min_hr_dt.hour
            # Fetching Minimum hour from all the end date records.
            self._cr.execute(
                """select end_date
                         as mn from car_reservation cr where vehicle_id = %s
                         and id in %s group by cr.id order by mn limit 1""",
                (vehicle_rec.id, tuple(reservation_recs.ids),),
            )
            min_en_hr_dt = self._cr.dictfetchone()
            utc_timestamp = pytz.utc.localize(
                min_en_hr_dt.get("mn"), is_dst=False
            )  # UTC = no DST
            min_en_hr_dt = utc_timestamp.astimezone(pytz.timezone(tz_name))
            min_en_hour = min_en_hr_dt.hour
            # Default assigning min.hours and date
            # Assigning Min.hour either of start date or end date.
            if (min_st_hour and min_en_hour) and min_st_hour > min_en_hour:
                min_hr_dt = min_en_hr_dt
            final_min_hr_dt = min_hr_dt
            final_min_hr = int(final_min_hr_dt.strftime("%H"))
            # Fetching Maximum hour from all the start date records.
            self._cr.execute(
                """select start_date
                         as mx from car_reservation cr where vehicle_id = %s
                         and id in %s group by cr.id
                         order by mx desc limit 1""",
                (vehicle_rec.id, tuple(reservation_recs.ids),),
            )
            max_hr_dt = self._cr.dictfetchone()
            utc_timestamp = pytz.utc.localize(
                max_hr_dt.get("mx"), is_dst=False
            )  # UTC = no DST
            max_hr_dt = utc_timestamp.astimezone(pytz.timezone(tz_name))
            max_st_hour = max_hr_dt.hour
            # Fetching Maximum hour from all the end date records.
            self._cr.execute(
                """select end_date
                         as mx from car_reservation cr where vehicle_id = %s
                         and id in %s group by cr.id
                         order by mx desc limit 1""",
                (vehicle_rec.id, tuple(reservation_recs.ids),),
            )
            max_en_hr_dt = self._cr.dictfetchone()
            utc_timestamp = pytz.utc.localize(
                max_en_hr_dt.get("mx"), is_dst=False
            )  # UTC = no DST
            max_en_hr_dt = utc_timestamp.astimezone(pytz.timezone(tz_name))
            max_en_hour = max_en_hr_dt.hour
            # Default assigning max.hours and date

            # Assigning Max.hour either of start date or end date records.
            if (max_st_hour and max_en_hour) and max_st_hour < max_en_hour:
                # max_hour = max_en_hour
                max_hr_dt = max_en_hr_dt
            # Time zone Conversion.
            final_max_hr_dt = max_hr_dt
            final_max_hr = int(final_max_hr_dt.strftime("%H"))
            final_min_hr = 1
            final_max_hr = 24
            # Iterating while to print Time finally in columns.
            s = True
            while s:
                if final_min_hr == final_max_hr:
                    s = False
                # if hours cross 24 hours then resetting it to 1.
                if final_min_hr > 24:
                    final_min_hr = 1
                # '{:02}'.format => for making '1' into '01' format.
                disp_time = format(final_min_hr, ".2f")
                final_disp_time = str(disp_time).zfill(5)
                worksheet.write(row, col, final_disp_time)
                vehicle_time_dict[str(final_min_hr).zfill(2)] = [col]
                final_min_hr = final_min_hr + 1
                col += 1
            # Relevant reservations records of vehicle only.
            vehicle_reserv_recs = reservation_recs.filtered(
                lambda r: r.vehicle_id == vehicle_rec
            )

            worksheet.merge_range(
                0, 0, 0, col, brand_name + " " + sheet_name, merge_format
            )
            worksheet.set_column(0, 0, 12)

            # Now Iterating reservation records and fetching row and col.from
            # dictionary to merge/ write into the cells.
            for vehice_reserve_rec in vehicle_reserv_recs:
                # Fetching Dates
                veh_res_st_dt_str_frmt = vehice_reserve_rec.start_date
                utc_timestamp = pytz.utc.localize(
                    veh_res_st_dt_str_frmt, is_dst=False
                )  # UTC = no DST
                veh_res_st_dt_str_frmt = utc_timestamp.astimezone(
                    pytz.timezone(tz_name)
                )
                veh_res_en_dt_str_frmt = vehice_reserve_rec.end_date
                utc_timestamp = pytz.utc.localize(
                    veh_res_en_dt_str_frmt, is_dst=False
                )  # UTC = no DST
                veh_res_en_dt_str_frmt = utc_timestamp.astimezone(
                    pytz.timezone(tz_name)
                )
                disp_veh_res_st_dt = datetime.strftime(
                    veh_res_st_dt_str_frmt, df)
                disp_veh_res_en_dt = datetime.strftime(
                    veh_res_en_dt_str_frmt, df)
                # Fetching row no from stored dictionary.
                row_no1 = vehicle_date_dict[disp_veh_res_st_dt]
                row_no2 = vehicle_date_dict[disp_veh_res_en_dt]
                # Fetching Times.
                veh_res_st_time = datetime.strftime(
                    veh_res_st_dt_str_frmt, "%H")
                veh_res_en_time = datetime.strftime(
                    veh_res_en_dt_str_frmt, "%H")
                # fetching driver name first from reservation record
                # if its not there fetching from reservation's vehicle's
                # driver record.
                driver_name = (vehice_reserve_rec.driver_id and
                               vehice_reserve_rec.driver_id.name or
                               vehice_reserve_rec.vehicle_id and
                               vehice_reserve_rec.vehicle_id.driver_id and
                               vehice_reserve_rec.vehicle_id.driver_id.name or
                               "-")
                # If both date and time are same means need to write in
                # single row.pickup
                if (disp_veh_res_st_dt == disp_veh_res_en_dt and
                        veh_res_st_time == veh_res_en_time):
                    col_no1 = vehicle_time_dict[veh_res_st_time]
                    worksheet.write(row_no1[0], col_no1[0],
                                    driver_name or "-", merge_cell_format)
                else:
                    col_no1 = vehicle_time_dict[veh_res_st_time]
                    col_no2 = vehicle_time_dict[veh_res_en_time]
                    worksheet.merge_range(
                        row_no1[0],
                        col_no1[0],
                        row_no2[0],
                        col_no2[0],
                        driver_name or "",
                        merge_cell_format)

        workbook.close()
        buf = base64.encodebytes(open("/tmp/" + file_path, "rb").read())
        try:
            if buf:
                os.remove(file_path + ".xlsx")
        except OSError:
            pass
        # creating a record as in v10 without this its not allowing to print
        # .xls report perfectly.(js error).
        wiz_rec = wiz_download_rep_obj.create(
            {"file": buf, "name": "Car Reservation Details.xlsx"}
        )
        form_view = self.env.ref(
            "car_reservation.wiz_reserve_details_download_wiz")
        if wiz_rec and form_view:
            return {
                "name": _("Car Reservation Report Download File"),
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_id": wiz_rec.id,
                "res_model": "wiz.download.reserve.report",
                "views": [(form_view.id, "form")],
                "view_id": form_view.id,
                "target": "new",
            }
        else:
            return {}


class WizDownloadReserveRep(models.TransientModel):
    """Wizard Download Reservation Report Transient Model."""

    _name = "wiz.download.reserve.report"
    _description = "Wizard Download Reservation Details Report"

    file = fields.Binary("Click On Download Link To Download Xlsx File",
                         readonly=True)
    name = fields.Char(string="File Name", size=32)
