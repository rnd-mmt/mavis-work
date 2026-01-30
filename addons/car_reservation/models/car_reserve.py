# See LICENSE file for full copyright and licensing details.
"""Car Reservation Model."""

import logging
import requests
from odoo import SUPERUSER_ID, _, api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def reservation_geo_find(addr, apikey=False):
    """Geolocation find."""
    if not addr:
        return None

    if not apikey:
        raise UserError(
            _(
                """API key for GeoCoding (Places) required.\n
                          Save this key in System Parameters with key:
                          google.api_key_geocode, value: <your api key>
                          Visit https://developers.google.com/maps/\
                          documentation/geocoding/get-api-key for more
                          information."""
            )
        )

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    try:
        result = requests.get(
            url, params={"sensor": "false", "address": addr, "key": apikey}
        ).json()
    except Exception as e:
        raise UserError(
            _(
                "Cannot contact geolocation servers. \
              Please make sure that your Internet connection \
              is up and running (%s)."
            )
            % e
        )

    if result["status"] != "OK":
        if result.get("error_message"):
            _logger.error(result["error_message"])
            error_msg = _(
                "Unable to geolocate, received the error:\n%s"
                "\n\nGoogle made this a paid feature.\n"
                "You should first enable billing on your \
                          Google account.\n"
                "Then, go to Developer Console, and enable \
                          the APIs:\n"
                "Geocoding, Maps Static, Maps Javascript.\n" %
                result["error_message"]
            )
            raise UserError(error_msg)

    try:
        geo = result["results"][0]["geometry"]["location"]
        return float(geo["lat"]), float(geo["lng"])
    except (KeyError, ValueError):
        return None


def reservation_geo_query_address(street=None, zip=None, city=None,
                                  state=None, country=None):
    """Method to set address."""
    if (country and "," in country and (country.endswith(" of") or
                                        country.endswith(" of the"))):
        # put country qualifier in front, otherwise GMap gives wrong results,
        # e.g. 'Congo, Democratic Republic of the' => 'Democratic Republic of
        # the Congo'
        country = "{1} {0}".format(*country.split(",", 1))
    return tools.ustr(", ".join(field
                                for field in [
                                    street,
                                    ("{} {}".format(zip or "",
                                                    city or "")).strip(),
                                    state,
                                    country,
                                ] if field))


class CarReservation(models.Model):
    """Car Reservation Model."""

    _name = "car.reservation"
    _description = "Car Reservation "

    name = fields.Char(
        "Name",
        help="The name of the reservation",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        help="Select Vehicle for the reservation",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    emp_type = fields.Selection(
        [("contacts", "Contacts"), ("employee", "Employee")],
        "Contacts/Employees",
        default="employee",
        help="choose Person is Partner or Employee !",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contacts",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    employee_id = fields.Many2one(
        "hr.employee",
        "Employee",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    approvar_id = fields.Many2one(
        "res.users", "Approver", readonly=True,
        states={"draft": [("readonly", False)]})
    driver_id = fields.Many2one("res.partner", "Driver",
                                readonly=True,
                                states={"draft": [("readonly", False)]})
    start_date = fields.Datetime(
        string="Start Time",
        default=fields.Datetime.now(),
        help="Starting time of reservation",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    end_date = fields.Datetime(
        string="End Time",
        help="Ending time of reservation",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [
            ("draft", "New"),
            ("approved", "Approved"),
            ("reserved", "Reserved"),
            ("cancel", "Cancelled"),
            ("done", "Done"),
        ],
        string="State",
        default="draft",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    pickup_location_id = fields.Many2one(
        "reservation.location",
        "Pick-up Location",
        readonly=True,
        ondelete="restrict",
        states={"draft": [("readonly", False)]},
    )
    latitude = fields.Float(
        related="pickup_location_id.partner_latitude",
        string="Location Latitude",
        digits=(4, 9))
    longitude = fields.Float(
        related="pickup_location_id.partner_longitude",
        string="Location longitude",
        digits=(4, 9))
    drop_location_id = fields.Many2one(
        "reservation.location",
        "Drop Location",
        readonly=True,
        ondelete="restrict",
        states={"draft": [("readonly", False)]},
    )
    # Changed Below field type to fix redirect address on google map issue
    drop_latitude = fields.Float(
        related="drop_location_id.partner_latitude",
        string="Drop Location Latitude")
    drop_longitude = fields.Float(
        related="drop_location_id.partner_longitude",
        string="Drop Location longitude")
    notes = fields.Text(
        string="Details", readonly=True,
        states={"draft": [("readonly", False)]})
    value = fields.Float(string="Kilometer (Distance)")
    reservation_no = fields.Char(string="Reservation Number",
                                 copy=False)

    pick_street = fields.Char(related="pickup_location_id.street",
                              string="Pick Location Street")
    pick_street2 = fields.Char(related="pickup_location_id.street2",
                               string="Pick Location Street2")
    pick_zip = fields.Char(related="pickup_location_id.zip",
                           string="Pick Location Zip")
    pick_city = fields.Char(related="pickup_location_id.city",
                            string="Pick Location City")
    pick_state_id = fields.Many2one(related="pickup_location_id.state_id",
                                    # "res.country.state",
                                    string="Pick Location State",
                                    ondelete="restrict")
    pick_country_id = fields.Many2one(related="pickup_location_id.country_id",
                                      # "res.country",
                                      string="Pick Location Country",
                                      ondelete="restrict")
    pick_website = fields.Char(related="pickup_location_id.website",
                               string="Pick Location Website",
                               help="Website")
    pick_phone = fields.Char(related="pickup_location_id.phone",
                             string="Pick Location Phone")

    drop_street = fields.Char(related="drop_location_id.street",
                              string="Drop Location Street")
    drop_street2 = fields.Char(related="drop_location_id.street2",
                               string="Drop Location Street2")
    drop_zip = fields.Char(related="drop_location_id.zip",
                           string="Drop Location Zip")
    drop_city = fields.Char(related="drop_location_id.city",
                            string="Drop Location City")
    drop_state_id = fields.Many2one(related="drop_location_id.state_id",
                                    string="Drop Location State",
                                    ondelete="restrict")
    drop_country_id = fields.Many2one(related="drop_location_id.country_id",
                                      string="Drop Location Country",
                                      ondelete="restrict")
    drop_website = fields.Char(related="drop_location_id.website",
                               string="Drop Location Website",
                               help="Website")
    drop_phone = fields.Char(related="drop_location_id.phone",
                             string="Drop Location Phone")

    @api.onchange("emp_type")
    def onchange_emp_type(self):
        for emp_type in self:
            if emp_type.emp_type == "contacts":
                emp_type.employee_id = False
            else:
                emp_type.partner_id = False

    @api.constrains("value")
    def check_negative_value(self):
        """Method is used to check value."""
        for rec in self:
            if rec.value < 0.00:
                raise UserError(
                    _("Odometer Value Must be in Positive value !!"))

    @api.constrains("start_date", "end_date")
    def check_dates(self):
        """Method is used to validate the start_date and end_date."""
        for rec in self:
            if rec.start_date and rec.end_date and \
                    rec.start_date >= rec.end_date:
                raise UserError(
                    _("Start Time Should be less than the End Time!"))

    @api.onchange("vehicle_id")
    def onchange_vehicle_id(self):
        """Onchange method to update driver."""
        for rec in self:
            rec.driver_id = rec.vehicle_id.driver_id.id or False

    def get_emp_domain(self, emp_type):
        """Method to Search Reservation based on the domain."""
        rev = self
        reservations = False
        reservation_obj = self.env["car.reservation"]

        res = {
            "condition1": [
                ("id", "!=", rev.id),
                ("vehicle_id", "=", rev.vehicle_id.id),
                ("driver_id", "=", rev.driver_id.id),
                ("state", "in", ["approved", "reserved"]),
                ("employee_id", "=", rev.employee_id and
                    rev.employee_id.id or False,),
            ],
            "condition2": [
                ("id", "!=", rev.id),
                ("vehicle_id", "=", rev.vehicle_id.id),
                ("state", "in", ["approved", "reserved"]),
                ("driver_id", "=", rev.driver_id.id),
            ],
            "condition3": [
                ("id", "!=", rev.id),
                ("state", "in", ["approved", "reserved"]),
                ("vehicle_id", "=", rev.vehicle_id.id),
            ],
            "condition4": [
                ("id", "!=", rev.id),
                ("state", "in", ["approved", "reserved"]),
                ("driver_id", "=", rev.driver_id.id),
                ("employee_id", "=", rev.employee_id and
                    rev.employee_id.id or False,),
            ],
            "condition5": [
                ("id", "!=", rev.id),
                ("vehicle_id", "=", rev.vehicle_id.id),
                ("driver_id", "=", rev.driver_id.id),
                ("state", "in", ["approved", "reserved"]),
                ("partner_id", "=", rev.partner_id and
                    rev.partner_id.id or False,),
            ],
            "condition6": [
                ("id", "!=", rev.id),
                ("state", "in", ["approved", "reserved"]),
                ("driver_id", "=", rev.driver_id.id),
                ("partner_id", "=", rev.partner_id and
                    rev.partner_id.id or False,),
            ],
        }
        if emp_type == "employee":
            reservations = reservation_obj.search(res.get("condition1"))
            if not reservations:
                reservations = reservation_obj.search(res.get("condition2"))
            if not reservations:
                reservations = reservation_obj.search(res.get("condition3"))
            if not reservations:
                reservations = reservation_obj.search(res.get("condition4"))
        elif emp_type == "contacts":
            reservations = reservation_obj.search(res.get("condition5"))
            if not reservations:
                reservations = reservation_obj.search(res.get("condition2"))
            if not reservations:
                reservations = reservation_obj.search(res.get("condition3"))
            if not reservations:
                reservations = reservation_obj.search(res.get("condition6"))
        return reservations

    def check_reservation_validation(self):
        """Common method to check the reservation validation."""
        for rev in self:
            if rev.start_date and rev.end_date and rev.driver_id and \
                    rev.vehicle_id:
                reservations = rev.get_emp_domain(rev.emp_type)
                for reserv in reservations:
                    flag = False
                    if rev.start_date <= reserv.start_date <= rev.end_date:
                        flag = True
                    if rev.start_date <= reserv.end_date <= rev.end_date:
                        flag = True
                    if flag:
                        return reserv
        return False

    @api.model
    def create(self, vals):
        """Override create method to check reservation constraints."""
        reservation = super(CarReservation, self).create(vals)
        reserv = reservation.check_reservation_validation()
        if reserv:
            raise UserError(_("You can not add reservation with the same "
                              "Vehicle, Driver, Start Date and End Date for "
                              "same Employees Or Contacts. !! \n "
                              "Check Below Reservation : \n Name: %s \
                              ") % (reserv.name or ""))
        return reservation

    def write(self, vals):
        """Override create method to check reservation constraints."""
        res = super(CarReservation, self).write(vals)
        for reservation in self:
            if (vals.get("vehicle_id", False) or
                vals.get("driver_id", False) or
                vals.get("partner_id", False) or
                vals.get("employee_id", False) or
                    vals.get("state", False)):
                reserv = reservation.check_reservation_validation()
                if reserv:
                    raise UserError(_(
                        "You can not add reservation with the same "
                        "Vehicle, Driver, Start Date and End Date for "
                        "same Employees Or Contacts. !! \n"
                        "Check Reservation Details Below : \n"
                        "Name: %s ") % (reserv.name or ""))
        return res

    def unlink(self):
        """Method to Restrict approved or done reservations."""
        for rec in self:
            if rec.state in ("approved", "reserved", "done"):
                raise UserError(_(
                    "You can not delete reservations Which"
                    " is in Approved / Reserved / Done. !!"))
        return super(CarReservation, self).unlink()

    def update_state(self):
        """Update state Method.

        Common method will call on click on buttons available on
        form of reservation.
        """
        context = self._context
        odometer_obj = self.env["fleet.vehicle.odometer"]
        template = self.env.ref(
            "car_reservation.custom_car_reservation_template")
        for rec in self:
            state_to_update = context.get("state", False)
            if (state_to_update == "approved" and
                rec._uid != SUPERUSER_ID and
                    rec._uid != rec.approvar_id.id):
                raise UserError(
                    _("Only Reservation Approver can approve "
                        "this Reservation !"))
            elif state_to_update == "reserved":
                # Checking if vehicle is already reserved in this specific
                # time it will not allow to reserve / overlap it again.
                domain = [
                    ("vehicle_id", "=", rec.vehicle_id.id),
                    ("start_date", "<=", rec.end_date),
                    ("end_date", ">=", rec.start_date),
                    ("id", "!=", rec.id),
                    ("state", "=", "reserved"),
                ]
                if rec.search_count(domain):
                    raise UserError(
                        _("Car %s is already reserved !" % rec.vehicle_id.name)
                    )
                if rec.vehicle_id:
                    rec.vehicle_id.state = "reserved"
            elif state_to_update == "done" and rec.vehicle_id:
                data = {
                    "value": rec.value,
                    "date": fields.Datetime.now(),
                    "pickup_location_id": rec.pickup_location_id and
                    rec.pickup_location_id.id or False,
                    "drop_location_id": rec.drop_location_id and
                    rec.drop_location_id.id or False,
                    "vehicle_id": rec.vehicle_id and
                    rec.vehicle_id.id or False,
                }
                # Create odometer history
                odometer_obj.create(data)
                if rec.vehicle_id:
                    rec.vehicle_id.state = "available"
            if state_to_update == "approved" and not rec.reservation_no:
                rec.reservation_no = (
                    self.env["ir.sequence"].next_by_code(
                        "car.reservation") or ""
                )
            if state_to_update:
                rec.state = state_to_update
            if state_to_update == "done" and template:
                template.send_mail(rec.id, force_send=True,
                                   raise_exception=False)


class FleetVehicle(models.Model):
    """Fleet Vehicle Model."""

    _inherit = "fleet.vehicle"

    def _compute_count_vehicle_reservations(self):
        reservation_obj = self.env["car.reservation"]
        for record in self:
            record.reservation_count = reservation_obj.search_count([
                ("vehicle_id", "=", record.id)])

    reservation_count = fields.Integer(
        compute="_compute_count_vehicle_reservations",
        string="Reservations")
    # We added below state field same as our contributed module
    # fleet_operations, fleet_rent because we need to make it
    # compatible to work with that modules.
    state = fields.Selection([
        ("inspection", "Draft"),
        ("in_progress", "In Service"),
        ("contract", "On Contract"),
        ("rent", "On Rent"),
        ("complete", "Completed"),
        ("released", "Released"),
        ("reserved", "Reserved"),
        ("available", "Available"),
        ("write-off", "Write-Off"), ],
        string="Vehicle Status",
        default="inspection",)

    # Override below fields from the base fleet module
    odometer = fields.Float(
        compute="_compute_get_odometer",
        string="Last Odometer",
        help="Odometer measure of the vehicle at " "the moment of this log",
    )

    def _compute_get_odometer(self):
        """Compute method to calculate total odometer."""
        odometer_obj = self.env["fleet.vehicle.odometer"]
        for record in self:
            vehicle_odometers = odometer_obj.search(
                [("vehicle_id", "=", record.id)], order="value desc"
            )
            if vehicle_odometers:
                record.odometer = sum(
                    odom.value for odom in vehicle_odometers) or 0.0
            else:
                record.odometer = 0


class ReservationLocation(models.Model):
    """Reservation Location Model."""

    _name = "reservation.location"
    _description = "Reservation Location"

    name = fields.Char("Location")
    # Changed Below field type to fix redirect address on google map issue
    partner_latitude = fields.Float("Latitude", digits=(4, 9))
    partner_longitude = fields.Float("Longitude", digits=(4, 9))
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one(
        "res.country.state", string="State", ondelete="restrict")
    country_id = fields.Many2one(
        "res.country", string="Country", ondelete="restrict")
    website = fields.Char(help="Website")
    phone = fields.Char()

    @classmethod
    def _reservation_geo_localize(cls, apikey, street="", zip="", city="",
                                  state="", country=""):
        """Return the Geo localise information."""
        geo_info = reservation_geo_query_address(
            street=street, zip=zip, city=city, state=state, country=country)

        result = reservation_geo_find(geo_info, apikey)

        if result is None:
            geo_info = reservation_geo_query_address(
                city=city, state=state, country=country)
            result = reservation_geo_find(geo_info, apikey)
        return result

    def geo_localize(self):
        """Replicate same method from base module to get latitude,longitude."""
        # We need country names in English below
        apikey = (
            self.env["ir.config_parameter"].sudo().get_param(
                "web_google_maps.api_key")
        )
        for partner in self.with_context(lang="en_US"):
            result = partner._reservation_geo_localize(
                apikey,
                partner.street,
                partner.zip,
                partner.city,
                partner.state_id.name,
                partner.country_id.name,
            )

            if result:
                partner.write({
                    "partner_latitude": result[0],
                    "partner_longitude": result[1]
                })
        return True


class FleetVehicleOdometer(models.Model):
    """Fleet Vehicle Odometer Model."""

    _inherit = "fleet.vehicle.odometer"

    pickup_location_id = fields.Many2one("reservation.location",
                                         ondelete="restrict",
                                         string="Pick-up Location")
    drop_location_id = fields.Many2one("reservation.location",
                                       ondelete="restrict",
                                       string="Drop Location")

    @api.constrains("value")
    def check_negative_value(self):
        """Method is used to check value."""
        for rec in self:
            if rec.value < 0.00:
                raise UserError(_("Odometer Value Must be"
                                  " in Positive value !"))
