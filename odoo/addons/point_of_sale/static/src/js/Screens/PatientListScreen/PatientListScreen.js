odoo.define('point_of_sale.PatientListScreen', function (require) {
    'use strict';

    const { debounce } = owl.utils;
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const { isRpcError } = require('point_of_sale.utils');
    const { useAsyncLockedMethod } = require('point_of_sale.custom_hooks');

    const profilTypeMap = {
        'all': { label: 'C-', showAssurance: true, showPension: false },
        'fonc_activity': { label: 'C-', showAssurance: true, showPension: false },
        'fonc_pensioner': { label: 'R-', showAssurance: true, showPension: true },
        'pec_privee': { label: '', showAssurance: true, showPension: false },
        'other': { label: '', showAssurance: false, showPension: false },
        'arovy': { label: '', showAssurance: true, showPension: false },
        'smi': { label: '', showAssurance: true, showPension: false },
        'pecgr': { label: '', showAssurance: true, showPension: false },
        'remboursement': { label: '', showAssurance: true, showPension: false },
    };

    class PatientListScreen extends PosComponent {
        constructor() {
            super(...arguments);
            this.lockedSaveChanges = useAsyncLockedMethod(this.saveChanges);

            useListener('click-save', () => this.createPatient());
            //  this.env.bus.trigger('save-customer'));
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
                patient_gender: 'all',
                patient_label: '',
                profil_type: 'all',
                patient_assurance: '',
                patient_pension: '',
                patient_pricelist: 'Standard',
                patient_person_contact: '',
                patient_marital_status: 'all',

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

        // clickPatient(event) {
        //     const partner = event.detail.patient;
        //     this.state.selectedPatient = (this.state.selectedPatient === partner) ? null : partner;
        //     this.render();
        // }

        clickPatient(event) {
            const partner = event.detail.patient;
            // S’il est déjà sélectionné, on le désélectionne
            if (this.state.selectedPatient && this.state.selectedPatient.id === partner.id) {
                this.state.selectedPatient = null;
            } else {
                this.state.selectedPatient = partner;
            }
            console.log(" SELECTED PATIENT ----------- ", this.state.selectedPatient);
            this.render();
        }

        selectPatientForService(patient) {
            // Définir ce patient dans l’environnement POS (ActionParWidget)
            this.env.pos.get_order().set_client(patient);
            this.showPopup('ConfirmPopup', {
                title: this.env._t('Patient sélectionné'),
                body: this.env._t(`${patient.name} est maintenant défini comme patient actif.`),
            });
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

        async activateEditMode(event) {
            const check = this.validateBeforeCreate();
            if (!check.ok) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t("Champs obligatoires manquants"),
                    body: this.env._t(check.message),
                });
                return;
            }

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

        // async onInputChange(ev, field) {
        //     this.state[field] = ev.target.value;
        //     await this.fetchSimilarPatients();
        //     this.render();
        // }
        highlightContactGroup() {
            const phone = this.state.patient_phone || "";
            const address = this.state.patient_adress || "";
            const cin = this.state.gov_code || "";

            const fields = this.el.querySelectorAll('.group-required');

            // Si aucun rempli → les 3 colorés
            if (!phone && !address && !cin) {
                fields.forEach(f => f.classList.add("required-field"));
                return;
            }

            // Si au moins 1 rempli → seul celui rempli est coloré
            fields.forEach(f => {
                const fieldName = f === fields[0] ? 'patient_phone'
                    : f === fields[1] ? 'patient_adress'
                        : 'gov_code';

                if (this.state[fieldName]) {
                    f.classList.add("required-field");
                } else {
                    f.classList.remove("required-field");
                }
            });
        }

        mounted() {
            this.highlightContactGroup();
        }

        validateBeforeCreate() {
            const errors = [];
            const errors_new = [];

            // Champs obligatoires stricts
            if (!this.state.patient_name?.trim()) errors.push("Nom du patient");
            if (!this.state.patient_birthday?.trim()) errors.push("Date de naissance");
            if (!this.state.patient_gender || this.state.patient_gender === "all") errors.push("Sexe");

            // Groupe (au moins un rempli)
            if (
                !this.state.patient_phone?.trim() &&
                !this.state.patient_adress?.trim() &&
                !this.state.gov_code?.trim()
            ) {
                errors_new.push("\n Au moins un des champs suivants doit être rempli : Téléphone, Adresse, CIN.");
            }

            // Si erreurs obligatoires strictes
            if (errors.length > 0) {
                return {
                    ok: false,
                    message: "Veuillez remplir les champs obligatoires :\n- " + errors.join("\n- ") + errors_new
                };
            }

            return { ok: true };
        }


        async onInputChange(ev, field) {
            this.state[field] = ev.target.value;

            this.highlightContactGroup();
            if (field === 'profil_type') {
                const map = profilTypeMap[this.state.profil_type]
                    || { label: '', showAssurance: true, showPension: false };
                this.state.payment_label = map.label;   // C- ou R-
                this.state.show_patient_assurance = map.showAssurance;  // afficher input assurance ?
                this.state.show_patient_pension = map.showPension;  // afficher pension ?
            }
            await this.fetchSimilarPatients();
            this.render();
        }

        async fetchSimilarPatients() {
            try {
                const domain = [];
                if (this.state.patient_name && this.state.patient_name.trim() !== "") {
                    domain.push(['name', 'ilike', this.state.patient_name]);
                }
                if (this.state.patient_code && this.state.patient_code.trim() !== "") {
                    domain.push(['code', 'ilike', this.state.patient_code]);
                }
                if (this.state.patient_gender &&
                    this.state.patient_gender.trim() !== "" &&
                    this.state.patient_gender.trim() !== "all"
                ) {
                    domain.push(['gender', 'ilike', this.state.patient_gender]);
                }
                if (this.state.patient_phone && this.state.patient_phone.trim() !== "") {
                    domain.push(['mobile', 'ilike', this.state.patient_phone]);
                }
                if (this.state.patient_email && this.state.patient_email.trim() !== "") {
                    domain.push(['email', 'ilike', this.state.patient_email]);
                }
                if (this.state.patient_street && this.state.patient_street.trim() !== "") {
                    domain.push(['street', 'ilike', this.state.patient_street]);
                }
                if (this.state.patient_marital_status &&
                    this.state.patient_marital_status.trim() !== "" &&
                    this.state.patient_marital_status.trim() !== "all") {
                    domain.push(['marital_status', 'ilike', this.state.patient_marital_status]);
                }
                if (this.state.patient_birthday && this.state.patient_birthday.trim() !== "") {
                    domain.push(['birthday', '=', this.state.patient_birthday]);
                }

                if (this.state.patient_assurance && this.state.patient_assurance.trim() !== "") {
                    domain.push(['assurance', '=', this.state.patient_assurance]);
                }

                const res = await this.rpc({
                    model: 'hms.patient',
                    method: 'search_read',
                    domain: domain,
                    fields: ['id', 'name', 'code', 'birthday', 'gender', 'street', 'mobile', 'create_date'],
                    limit: 60,
                });

                this.state.similar_patients = res;
            } catch (error) {
                console.error('Erreur recherche patient similaire', error);
            }
        }

        async createPatient() {
            console.log("-------------- ----------------");
            console.log(" ***************CREATE PATIENT*****************");
            const check = this.validateBeforeCreate();
            if (!check.ok) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t("Champs obligatoires manquants"),
                    body: this.env._t(check.message),
                });
                return;
            }

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
            try { // 1️⃣ Création du patient 
                const partnerId = await this.rpc({
                    model: 'hms.patient', method: 'create_from_ui', args: [data],
                });
                // // 2️⃣ Création automatique du Service Santé
                await this.rpc({
                    model: 'acs.health_service',
                    method: 'create_service_from_pos',
                    args: [{ patient_id: partnerId, }],
                });

                // 3️⃣ Mise à jour du POS
                await this.env.pos.load_new_partners();
                this.state.selectedPatient = this.env.pos.db.get_partner_by_id(partnerId);
                this.state.detailIsShown = false;
                this.render();
                await this.showPopup("ConfirmPopup", {
                    title: "Succès",
                    body: "Patient et Service Santé créés avec succès.",
                });
            } catch (error) {
                console.log('ee rr oo rr ', error);
                // if (isRpcError(error) && error.message.code < 0) {
                //     await this.showPopup('OfflineErrorPopup', {
                //         title: this.env._t('Offline'),
                //         body: this.env._t('Unable to save changes.'),
                //     });
                // } else { throw error; }
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
