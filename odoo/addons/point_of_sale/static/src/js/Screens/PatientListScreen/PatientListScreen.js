odoo.define('point_of_sale.PatientListScreen', function(require) {
    'use strict';

    const { debounce } = owl.utils;
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const { isRpcError } = require('point_of_sale.utils');
    const { useAsyncLockedMethod } = require('point_of_sale.custom_hooks');

    class PatientListScreen extends PosComponent {
        constructor() {
            super(...arguments);
            this.lockedSaveChanges = useAsyncLockedMethod(this.saveChanges);

            useListener('click-save', () => this.env.bus.trigger('save-customer'));
            useListener('click-edit', () => this.editPatient());
            useListener('save-changes', this.lockedSaveChanges);

            this.state = {
                query: '',
                selectedPatient: this.props.patient,
                detailIsShown: false,
                isEditMode: false,
                isNewPatient: false,

                // Champs principaux
                patient_code: '',
                patient_name: '',
                patient_phone: '',
                patient_mail: '',
                patient_adress: '',
                gov_code: '',

                // Champs supplémentaires
                patient_birthday: '',
                patient_gender: 'male',
                profil_type: 'other',
                patient_assurance: '',
                patient_pension: '',
                patient_pricelist: 'Standard',
                patient_contact_person: '',
                patient_marital_status: 'celibataire',

                // Patients similaires
                similar_patients: [],
            };

            this.updatePatientList = debounce(this.updatePatientList.bind(this), 70);
        }

        get patients() {
            if (this.state.query.trim()) {
                return this.env.pos.db.search_partner(this.state.query.trim());
            } else {
                return this.env.pos.db.get_partners_sorted(1000);
            }
        }

        get isNextButtonVisible() {
            return Boolean(this.state.selectedPatient);
        }

        get nextButton() {
            if (!this.props.patient) {
                return { command: 'set', text: this.env._t('Set Patient') };
            } else if (this.props.patient === this.state.selectedPatient) {
                return { command: 'deselect', text: this.env._t('Deselect Patient') };
            } else {
                return { command: 'set', text: this.env._t('Change Patient') };
            }
        }

        back() {
            if (this.state.detailIsShown) {
                this.state.detailIsShown = false;
                this.render();
            } else {
                this.props.resolve({ confirmed: false, payload: false });
                this.trigger('close-temp-screen');
            }
        }

        confirm() {
            this.props.resolve({ confirmed: true, payload: this.state.selectedPatient });
            this.trigger('close-temp-screen');
        }

        updatePatientList(event) {
            this.state.query = event.target.value;
            const patients = this.patients;
            if (event.code === 'Enter' && patients.length === 1) {
                this.state.selectedPatient = patients[0];
                this.clickNext();
            } else {
                this.render();
            }
        }

        clickPatient(event) {
            const partner = event.detail.patient;
            this.state.selectedPatient = (this.state.selectedPatient === partner) ? null : partner;
            this.render();
        }

        editPatient() {
            this.state.detailIsShown = true;
            this.state.isNewPatient = false;
            this.render();
        }

        clickNext() {
            this.state.selectedPatient = this.nextButton.command === 'set' ? this.state.selectedPatient : null;
            this.confirm();
        }

        activateEditMode(event) {
            const { isNewPatient } = event.detail;
            this.state.isEditMode = true;
            this.state.detailIsShown = true;
            this.state.isNewPatient = isNewPatient;
            this.render();
        }

        deactivateEditMode() {
            this.state.isEditMode = false;
            this.state.detailIsShown = false;
            this.render();
        }

        async onInputChange(ev, field) {
            this.state[field] = ev.target.value;
            await this.fetchSimilarPatients();
            this.render();
        }

        async fetchSimilarPatients() {
            try {
                const res = await this.rpc({
                    model: 'hms.patient',
                    method: 'search_read',
                    domain: [['name', 'ilike', this.state.patient_name || '']],
                    fields: ['id', 'name', 'code', 'birthday', 'gender', 'street', 'mobile', 'create_date'],
                    limit: 5,
                });
                this.state.similar_patients = res;
            } catch (error) {
                console.error('Erreur recherche patient similaire', error);
            }
        }

        async createPatient() {
            const data = {
                code: this.state.patient_code,
                name: this.state.patient_name,
                mobile: this.state.patient_phone,
                email: this.state.patient_mail,
                street: this.state.patient_adress,
                gov_code: this.state.gov_code,
                birthday: this.state.patient_birthday,
                gender: this.state.patient_gender,
                profil_type: this.state.profil_type,
                patient_assurance: this.state.profil_type !== 'other' ? this.state.patient_assurance : undefined,
                patient_pension: this.state.profil_type === 'fonc_pensioner' ? this.state.patient_pension : undefined,
                contact_person: this.state.patient_contact_person,
                marital_status: this.state.patient_marital_status,
                pricelist: this.state.patient_pricelist,
            };

            try {
                const partnerId = await this.rpc({
                    model: 'res.partner',
                    method: 'create_from_ui',
                    args: [data],
                });
                await this.env.pos.load_new_partners();
                this.state.selectedPatient = this.env.pos.db.get_partner_by_id(partnerId);
                this.state.detailIsShown = false;
                this.render();
            } catch (error) {
                if (isRpcError(error) && error.message.code < 0) {
                    await this.showPopup('OfflineErrorPopup', {
                        title: this.env._t('Offline'),
                        body: this.env._t('Unable to save changes.'),
                    });
                } else {
                    throw error;
                }
            }
        }

        cancelEdit() {
            this.deactivateEditMode();
        }
    }

    PatientListScreen.template = 'PatientListScreen';
    Registries.Component.add(PatientListScreen);

    return PatientListScreen;
});
