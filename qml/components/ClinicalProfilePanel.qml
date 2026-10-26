
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import ".."

HgCard {
    id: root
    implicitHeight: outerCol.implicitHeight + 30

    // What the patient reported at this visit. Kept as a plain list so it
    // can be written straight into the encounter record.
    property var symptoms: []

    // Drug names as free text, matched by the interaction engine.
    property var medications: []

    function _num(t) {
        var s = (t || "").trim()
        if (!s.length) return null
        var n = Number(s.replace(",", "."))
        return isFinite(n) ? n : null
    }

    function _put(m, k, t) {
        var v = _num(t)
        if (v !== null) m[k] = v
    }

    function _yn(idx) {
        return idx === 1 ? 0 : idx === 2 ? 1 : null
    }

    // Chips mirror what the clinician has typed for this patient. They
    // stay empty until the form is filled, which is the honest signal
    // that nothing is known yet.
    property var profileChips: {
        var arr = []
        var a = _num(ageF.text)
        if (a && a > 0) arr.push("Age " + Math.round(a))
        if (sexC.currentIndex === 1) arr.push("Female")
        else if (sexC.currentIndex === 2) arr.push("Male")
        var h = _num(heightF.text)
        if (h && h > 0) arr.push("Height " + Math.round(h) + " cm")
        var w = _num(weightF.text)
        if (w && h && h > 0) arr.push("BMI " + (w / Math.pow(h / 100, 2)).toFixed(1))
        return arr
    }

    function contextMap() {
        var m = {}
        if (root.symptoms.length) {
            m["symptoms"] = root.symptoms
            m["symptoms_present"] = true
        }
        if (root.medications.length)
            m["current_medications"] = root.medications
        _put(m, "age_years", ageF.text)
        _put(m, "height_cm", heightF.text)

        // Sex stays absent until chosen: it selects reference ranges and
        // gates several risk models, so a default would be a silent claim.
        if (sexC.currentIndex === 1) m["sex_at_birth"] = "female"
        else if (sexC.currentIndex === 2) m["sex_at_birth"] = "male"

        _put(m, "weight_kg", weightF.text)
        _put(m, "waist_cm", waistF.text)
        _put(m, "neck_cm", neckF.text)
        _put(m, "systolic_bp", sbpF.text)
        _put(m, "diastolic_bp", dbpF.text)
        _put(m, "heart_rate", hrF.text)

        if (smokeC.currentIndex === 1) m["smoking"] = 0
        else if (smokeC.currentIndex === 2) m["smoking"] = 1

        _put(m, "cigarettes_per_day", cigsF.text)
        _put(m, "smoking_years", yrsF.text)
        _put(m, "quit_years", quitF.text)

        if (actC.currentIndex === 1) m["physical_activity"] = 1
        else if (actC.currentIndex === 2) m["physical_activity"] = 0

        if (vegC.currentIndex === 1) m["daily_fruit_veg"] = 1
        else if (vegC.currentIndex === 2) m["daily_fruit_veg"] = 0

        if (fastC.currentIndex === 1) m["fasting"] = true
        else if (fastC.currentIndex === 2) m["fasting"] = false

        if (pregC.currentIndex === 1) m["pregnant"] = false
        else if (pregC.currentIndex === 2) m["pregnant"] = true

        if (htnOn.checked) { m["hypertension"] = 1; m["bp_treated"] = 1 }
        if (dmOn.checked) m["diabetes_flag"] = 1
        if (afOn.checked) m["af"] = 1
        if (hfOn.checked) m["hf"] = 1
        if (copdOn.checked) m["copd"] = 1
        if (strokeOn.checked) m["stroke"] = 1
        if (vteOn.checked) m["prior_vte"] = 1
        if (caOn.checked) m["active_cancer"] = 1
        if (ckdOn.checked) m["ckd"] = 1
        if (liverOn.checked) m["liver_disease"] = 1
        if (retinoOn.checked) m["retinopathy"] = 1

        if (fhDmOn.checked) m["family_history_dm"] = 1
        if (fhCadOn.checked) m["family_history_cad"] = 1
        if (fhStrokeOn.checked) m["family_history_stroke"] = 1
        if (fhCrcOn.checked) m["family_history_crc"] = 1
        if (fhLungOn.checked) m["family_history_lung_ca"] = 1
        if (fhHccOn.checked) m["family_history_hcc"] = 1

        if (postmenoOn.checked) m["postmenopausal"] = 1
        if (gdmOn.checked) m["gestational_dm"] = 1
        if (estrogenOn.checked) m["current_estrogen_use"] = 1

        if (snoreOn.checked) m["snoring_loud"] = 1
        if (tiredOn.checked) m["daytime_tiredness"] = 1
        if (apneaOn.checked) m["observed_apnea"] = 1

        if (mobilityOn.checked) m["reduced_mobility_3d"] = 1
        if (surgOn.checked) m["recent_trauma_surgery_1mo"] = 1
        if (hormoneOn.checked) m["ongoing_hormone_treatment"] = 1

        return m
    }

    function reset() {
        var tfs = [ageF, heightF, weightF, waistF, neckF, sbpF, dbpF, hrF,
                   cigsF, yrsF, quitF]
        for (var i = 0; i < tfs.length; i++) tfs[i].text = ""

        root.symptoms = []
        root.medications = []
        sexC.currentIndex = 0
        smokeC.currentIndex = 0; actC.currentIndex = 0; vegC.currentIndex = 0
        fastC.currentIndex = 0; pregC.currentIndex = 0
        
        var chips = [htnOn, dmOn, afOn, hfOn, copdOn, strokeOn, vteOn, caOn, ckdOn, liverOn, retinoOn,
                     fhDmOn, fhCadOn, fhStrokeOn, fhCrcOn, fhLungOn, fhHccOn,
                     postmenoOn, gdmOn, estrogenOn, snoreOn, tiredOn, apneaOn, mobilityOn, surgOn, hormoneOn]
        for (var j = 0; j < chips.length; j++) chips[j].checked = false
    }

    function loadExample() {
        root.symptoms = ["fatigue", "nocturia", "oedema"]
        root.medications = ["metformin", "ace inhibitor"]
        ageF.text = "58"; sexC.currentIndex = 2; heightF.text = "174"
        weightF.text = "88"; waistF.text = "102"; neckF.text = "43"
        sbpF.text = "148"; dbpF.text = "94"; hrF.text = "82"

        smokeC.currentIndex = 2; cigsF.text = "15"; yrsF.text = "20"; quitF.text = "0"
        actC.currentIndex = 2; vegC.currentIndex = 2; fastC.currentIndex = 1

        htnOn.checked = true; dmOn.checked = true; copdOn.checked = true
        afOn.checked = false; hfOn.checked = false; strokeOn.checked = false
        vteOn.checked = false; caOn.checked = false; ckdOn.checked = false
        liverOn.checked = false; retinoOn.checked = false

        fhDmOn.checked = true; fhCadOn.checked = true; fhStrokeOn.checked = false

        snoreOn.checked = true; tiredOn.checked = true; apneaOn.checked = true

        postmenoOn.checked = false; gdmOn.checked = false; estrogenOn.checked = false
    }

    ColumnLayout {
        id: outerCol
        anchors.fill: parent
        anchors.margins: 16
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text { text: "CLINICAL CONTEXT"; color: Theme.muted; font.pixelSize: 10; font.bold: true; font.letterSpacing: 1.5 }
            Rectangle { 
                implicitWidth: optT.implicitWidth + 16; height: 20; radius: 10; color: "#F2F4F7"; border.color: Theme.border
                Text { id: optT; anchors.centerIn: parent; text: "OPTIONAL"; color: "#667085"; font.pixelSize: 8; font.bold: true } 
            }
            Item { Layout.fillWidth: true }

            Rectangle {
                implicitWidth: exRow.implicitWidth + 20; height: 32; radius: 16
                color: exMouse.containsMouse ? "#EFF8FF" : "transparent"
                border.color: exMouse.containsMouse ? "#84CAFF" : Theme.border
                Behavior on color { ColorAnimation { duration: 120 } }
                MouseArea { 
                    id: exMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                    onClicked: root.loadExample()
                    ToolTip.visible: hovered; ToolTip.text: "Auto-fill with a sample patient to test risk models"
                }
                Row { 
                    id: exRow; anchors.centerIn: parent; spacing: 6
                    Text { text: "✨"; font.pixelSize: 12 }
                    Text { text: "Load Example"; color: "#175CD3"; font.pixelSize: 11; font.bold: true }
                }
            }

            Text { text: "Exact inputs for risk models"; color: Theme.muted; font.pixelSize: 9 }
            ToolButton { 
                text: "↺"; ToolTip.visible: hovered; ToolTip.text: "Reset context"; onClicked: root.reset()
                contentItem: Text { text: "↺"; color: Theme.accent; font.pixelSize: 15; horizontalAlignment: Text.AlignHCenter }
                background: Rectangle { color: parent.hovered ? Theme.surfaceAlt : "transparent"; radius: 8 } 
            }
        }

        Flow {
            Layout.fillWidth: true; spacing: 8
            Repeater {
                model: root.profileChips
                delegate: Rectangle {
                    implicitWidth: chipT.implicitWidth + 18; height: 26; radius: 13
                    color: Theme.surfaceAlt; border.color: Theme.border
                    Text { id: chipT; anchors.centerIn: parent; text: modelData; color: Theme.muted; font.pixelSize: 9; font.bold: true }
                }
            }
        }

        SectionHeader { title: "👤 Patient" }
        GridLayout { Layout.fillWidth: true; columns: 4; columnSpacing: 12; rowSpacing: 10
            Field { id: ageF; label: "Age (years)"; ph: "—" }
            StyledCombo { id: sexC; label: "Sex"; items: ["—", "Female", "Male"] }
            Field { id: heightF; label: "Height (cm)"; ph: "—" }
        }

        // Laboratory numbers alone cannot separate diagnoses that share a
        // biochemical picture. Pica points at iron deficiency, nocturia at
        // renal disease, cold intolerance at hypothyroidism - none of which
        // any assay reports. These travel with the labs into the record so
        // later visits can be compared symptom by symptom.
        SectionHeader { title: "🗣 Presenting symptoms" }
        Flow {
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: [
                    "fatigue", "dyspnoea", "chest pain", "palpitations",
                    "dizziness", "pica", "cold intolerance", "heat intolerance",
                    "weight loss", "weight gain", "nocturia", "oedema",
                    "jaundice", "abdominal pain", "joint pain", "rash",
                    "fever", "night sweats", "bruising", "hair loss"
                ]
                delegate: Rectangle {
                    property bool picked: root.symptoms.indexOf(modelData) >= 0
                    height: 26
                    radius: 13
                    width: symptomText.implicitWidth + 22
                    color: picked ? Theme.accent : Theme.surfaceAlt
                    border.color: picked ? Theme.accent : Theme.border
                    Behavior on color { ColorAnimation { duration: 120 } }
                    Text {
                        id: symptomText
                        anchors.centerIn: parent
                        text: modelData
                        color: parent.picked ? "#ffffff" : Theme.muted
                        font.pixelSize: 10
                        font.bold: parent.picked
                    }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            var next = root.symptoms.slice()
                            var at = next.indexOf(modelData)
                            if (at >= 0) next.splice(at, 1)
                            else next.push(modelData)
                            root.symptoms = next
                        }
                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Field {
                id: otherSymptomF
                Layout.fillWidth: true
                label: "Other symptom"
                ph: "type and press Add"
            }
            HgButton {
                text: "Add"
                onClicked: {
                    var typed = otherSymptomF.text.trim().toLowerCase()
                    if (typed.length && root.symptoms.indexOf(typed) < 0) {
                        var next = root.symptoms.slice()
                        next.push(typed)
                        root.symptoms = next
                    }
                    otherSymptomF.text = ""
                }
            }
        }

        SectionHeader { title: "🩺 Vitals & Anthropometrics" }
        GridLayout { Layout.fillWidth: true; columns: 5; columnSpacing: 12; rowSpacing: 10
            Field { id: weightF; label: "Weight (kg)"; ph: "72" }
            Field { id: waistF; label: "Waist (cm)"; ph: "85" }
            Field { id: neckF; label: "Neck (cm)"; ph: "38" }
            Field { id: hrF; label: "Heart rate"; ph: "75" }
            Field { id: sbpF; label: "Systolic BP"; ph: "120" }
            Field { id: dbpF; label: "Diastolic BP"; ph: "80" }
        }

        // Medication is not background detail: a statin raises ALT, a
        // diuretic drops potassium, metformin masks B12 deficiency. The
        // engine already reasons about these, but until now nothing in the
        // interface let a clinician tell it what the patient is taking.
        SectionHeader { title: "💊 Current medication" }
        Flow {
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: [
                    "statin", "metformin", "insulin", "levothyroxine",
                    "ace inhibitor", "arb", "beta blocker", "diuretic",
                    "spironolactone", "amiodarone", "lithium", "methotrexate",
                    "corticosteroid", "nsaid", "ppi", "warfarin",
                    "heparin", "allopurinol", "iron supplement", "chemotherapy"
                ]
                delegate: Rectangle {
                    property bool picked: root.medications.indexOf(modelData) >= 0
                    height: 26
                    radius: 13
                    width: medText.implicitWidth + 22
                    color: picked ? Theme.violet : Theme.surfaceAlt
                    border.color: picked ? Theme.violet : Theme.border
                    Behavior on color { ColorAnimation { duration: 120 } }
                    Text {
                        id: medText
                        anchors.centerIn: parent
                        text: modelData
                        color: parent.picked ? "#ffffff" : Theme.muted
                        font.pixelSize: 10
                        font.bold: parent.picked
                    }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            var next = root.medications.slice()
                            var at = next.indexOf(modelData)
                            if (at >= 0) next.splice(at, 1)
                            else next.push(modelData)
                            root.medications = next
                        }
                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Field {
                id: otherDrugF
                Layout.fillWidth: true
                label: "Other medication"
                ph: "type and press Add"
            }
            HgButton {
                text: "Add"
                onClicked: {
                    var typed = otherDrugF.text.trim().toLowerCase()
                    if (typed.length && root.medications.indexOf(typed) < 0) {
                        var next = root.medications.slice()
                        next.push(typed)
                        root.medications = next
                    }
                    otherDrugF.text = ""
                }
            }
        }

        SectionHeader { title: "🚬 Lifestyle & Smoking" }
        GridLayout { Layout.fillWidth: true; columns: 4; columnSpacing: 12; rowSpacing: 10
            StyledCombo { id: smokeC; label: "Smoking status"; items: ["—", "No / never", "Current"] }
            Field { id: cigsF; label: "Cigs / day"; ph: "—"; enabled: smokeC.currentIndex === 2 }
            Field { id: yrsF; label: "Smoking years"; ph: "—"; enabled: smokeC.currentIndex > 0 }
            Field { id: quitF; label: "Quit years"; ph: "—"; enabled: smokeC.currentIndex === 1 }
            StyledCombo { id: actC; label: "Physical activity"; items: ["—", "Active", "Sedentary"] }
            StyledCombo { id: vegC; label: "Daily fruit/veg"; items: ["—", "Yes", "No"] }
            StyledCombo { id: fastC; label: "Fasting"; items: ["—", "Fasting", "Non-fasting"] }
            StyledCombo { id: pregC; label: "Pregnant"; items: ["—", "No", "Yes"] }
        }

        SectionHeader { title: "⚕️ Personal Medical History" }
        Flow { Layout.fillWidth: true; spacing: 8
            ToggleChip { id: htnOn; label: "Hypertension / BP meds" }
            ToggleChip { id: dmOn; label: "Diabetes" }
            ToggleChip { id: afOn; label: "Atrial Fibrillation" }
            ToggleChip { id: hfOn; label: "Heart Failure" }
            ToggleChip { id: copdOn; label: "COPD" }
            ToggleChip { id: strokeOn; label: "Stroke / TIA" }
            ToggleChip { id: vteOn; label: "Prior VTE (Clot)" }
            ToggleChip { id: caOn; label: "Active Cancer" }
            ToggleChip { id: ckdOn; label: "Kidney Disease (CKD)" }
            ToggleChip { id: liverOn; label: "Liver Disease" }
            ToggleChip { id: retinoOn; label: "Retinopathy" }
        }

        SectionHeader { title: "🧬 Family History (First-degree)" }
        Flow { Layout.fillWidth: true; spacing: 8
            ToggleChip { id: fhDmOn; label: "Diabetes" }
            ToggleChip { id: fhCadOn; label: "Heart Disease (CAD)" }
            ToggleChip { id: fhStrokeOn; label: "Stroke" }
            ToggleChip { id: fhCrcOn; label: "Colorectal Cancer" }
            ToggleChip { id: fhLungOn; label: "Lung Cancer" }
            ToggleChip { id: fhHccOn; label: "Liver Cancer (HCC)" }
        }

        SectionHeader { title: "🛌 Sleep & Mobility (Optional)" }
        Flow { Layout.fillWidth: true; spacing: 8
            ToggleChip { id: snoreOn; label: "Loud snoring" }
            ToggleChip { id: tiredOn; label: "Daytime tiredness" }
            ToggleChip { id: apneaOn; label: "Observed apnea" }
            ToggleChip { id: mobilityOn; label: "Reduced mobility (3d)" }
            ToggleChip { id: surgOn; label: "Recent surgery/trauma" }
            ToggleChip { id: hormoneOn; label: "Hormone treatment" }
        }

        SectionHeader { title: "♀️ Women's Health" }
        Flow { Layout.fillWidth: true; spacing: 8
            ToggleChip { id: postmenoOn; label: "Postmenopausal" }
            ToggleChip { id: gdmOn; label: "Gestational DM history" }
            ToggleChip { id: estrogenOn; label: "Current Estrogen / HRT" }
        }
    }

    Component.onCompleted: root.reset()

    component SectionHeader: RowLayout {
        property string title: ""
        Layout.fillWidth: true; spacing: 8
        Text { text: title; color: Theme.accent; font.pixelSize: 11; font.bold: true; font.letterSpacing: 1.2 }
        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border; opacity: 0.6 }
    }

    component Field: ColumnLayout {
        property alias text: tf.text
        property string label: ""; property string ph: ""
        spacing: 3
        Text { text: label; color: Theme.muted; font.pixelSize: 9 }
        HgField { id: tf; Layout.fillWidth: true; implicitHeight: 40; font.pixelSize: 12; placeholderText: ph; enabled: parent.enabled }
    }

    component StyledCombo: ColumnLayout {
        property alias currentIndex: cb.currentIndex
        property string label: ""; property var items: []
        spacing: 3
        Text { text: label; color: Theme.muted; font.pixelSize: 9 }
        Rectangle {
            Layout.fillWidth: true; implicitHeight: 42; radius: 12
            color: cb.pressed ? Theme.surfaceAlt : (cbHover.containsMouse ? "#FAFBFD" : Theme.surface)
            border.color: comboPopup.visible || cbHover.containsMouse ? Theme.accent : Theme.border
            border.width: comboPopup.visible ? 1.5 : 1
            Behavior on border.color { ColorAnimation { duration: 140 } }
            Behavior on color { ColorAnimation { duration: 140 } }
            MouseArea {
                id: cbHover; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                onClicked: comboPopup.open()
            }
            Text {
                anchors.left: parent.left; anchors.leftMargin: 14; anchors.verticalCenter: parent.verticalCenter
                text: cb.currentIndex >= 0 && cb.currentIndex < items.length ? items[cb.currentIndex] : "—"
                color: Theme.text; font.pixelSize: 12; elide: Text.ElideRight
            }
            Text {
                anchors.right: parent.right; anchors.rightMargin: 12; anchors.verticalCenter: parent.verticalCenter
                text: "▾"; font.pixelSize: 11; color: comboPopup.visible ? Theme.accent : Theme.muted
                rotation: comboPopup.visible ? 180 : 0
                Behavior on rotation { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
            }
            Popup {
                id: comboPopup; y: parent.height + 4; width: parent.width
                implicitHeight: Math.min(listContent.implicitHeight + 16, 280); padding: 6; modal: true
                closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
                background: Rectangle {
                    radius: 14; color: Theme.surface; border.color: Theme.border
                    Rectangle { anchors.fill: parent; radius: parent.radius; color: "transparent"; border.color: "#00000010"; border.width: 3; z: -1 }
                }
                contentItem: ListView {
                    id: listContent; clip: true; implicitHeight: contentHeight; model: items; currentIndex: cb.currentIndex
                    ScrollIndicator.vertical: ScrollIndicator {}
                    delegate: ItemDelegate {
                        id: opt; width: ListView.view ? ListView.view.width : comboPopup.width; implicitHeight: 38
                        highlighted: cb.currentIndex === index; hoverEnabled: true
                        contentItem: Text {
                            leftPadding: 12; rightPadding: 12; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight; font.pixelSize: 12
                            color: opt.highlighted ? Theme.accent : (opt.hovered ? Theme.text : Theme.muted)
                            text: modelData !== undefined && modelData !== null ? String(modelData) : ""; font.bold: opt.highlighted
                        }
                        background: Rectangle {
                            radius: 9; color: opt.highlighted ? "#EFF8FF" : (opt.hovered ? Theme.surfaceAlt : "transparent")
                            Behavior on color { ColorAnimation { duration: 100 } }
                        }
                        onClicked: { cb.currentIndex = index; comboPopup.close() }
                    }
                }
            }
        }
        ComboBox { id: cb; visible: false; model: items }
    }

    component ToggleChip: Rectangle {
        property string label: ""; property bool checked: false
        implicitWidth: chipText.implicitWidth + 26; height: 30; radius: 15
        color: checked ? "#ECFDF3" : Theme.surfaceAlt; border.color: checked ? "#75E0A7" : Theme.border
        Behavior on color { ColorAnimation { duration: 120 } }
        Behavior on border.color { ColorAnimation { duration: 120 } }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: parent.checked = !parent.checked }
        Text {
            id: chipText; anchors.centerIn: parent
            text: (checked ? "✓ " : "") + label; color: checked ? "#067647" : Theme.muted; font.pixelSize: 10; font.bold: true
        }
    }
}

