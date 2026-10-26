// SettingsPage.qml - Fully Structured, Fixed Geometry & Spacing
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "../components"
import ".."

Flickable {
    id: root
    contentWidth: width
    contentHeight: mainColumn.implicitHeight + 80
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    ScrollBar.vertical: ScrollBar {
        policy: ScrollBar.AsNeeded
        width: 6
        contentItem: Rectangle {
            implicitWidth: 6
            radius: 3
            color: Theme.muted
            opacity: 0.5
        }
    }

    // ========================= CENTRAL STATE =========================
    property int currentCategoryIndex: 0

    property var profileData: ({
        full_name: "",
        email: "",
        birth_date: "",
        sex: "Female",
        weight: null,
        height: null,
        waist: null,
        systolic_bp: null,
        diastolic_bp: null,
        heart_rate: null,
        sleep_hours: null,
        smoking: false,
        physical_activity: false,
        family_history_dm: false,
        family_history_cad: false,
        family_history_htn: false
    })
    property var originalData: ({})
    property bool isDirty: false

    // ========================= COMPUTED PROPERTIES =========================
    property int computedAge: {
        if (!profileData.birth_date || profileData.birth_date.length < 10) return 0
        try {
            var parts = profileData.birth_date.split("-")
            if (parts.length !== 3) return 0
            var year = parseInt(parts[0])
            var month = parseInt(parts[1])
            var day = parseInt(parts[2])
            if (isNaN(year) || isNaN(month) || isNaN(day)) return 0
            if (year < 1900 || year > 2026) return 0
            if (month < 1 || month > 12) return 0
            if (day < 1 || day > 31) return 0
            var today = new Date()
            var age = today.getFullYear() - year
            var m = today.getMonth() + 1 - month
            if (m < 0 || (m === 0 && today.getDate() < day)) age--
            return (age >= 0 && age <= 120) ? age : 0
        } catch (e) {
            return 0
        }
    }

    property real computedBMI: {
        var w = profileData.weight
        var h = profileData.height
        if (w && h && w > 0 && h > 0) {
            return w / Math.pow(h / 100, 2)
        }
        return 0
    }

    property string bmiCategory: {
        if (computedBMI <= 0) return "—"
        if (computedBMI < 18.5) return "Underweight"
        if (computedBMI < 25) return "Normal"
        if (computedBMI < 30) return "Overweight"
        if (computedBMI < 35) return "Obese I"
        if (computedBMI < 40) return "Obese II"
        return "Obese III"
    }

    property color bmiColor: {
        if (computedBMI <= 0) return Theme.muted
        if (computedBMI < 18.5) return Theme.warning
        if (computedBMI < 25) return Theme.success
        if (computedBMI < 30) return Theme.warning
        return Theme.danger
    }

    property bool birthDateValid: {
        if (!profileData.birth_date) return true
        var regex = /^\d{4}-\d{2}-\d{2}$/
        if (!regex.test(profileData.birth_date)) return false
        return computedAge > 0
    }

    // ========================= MAIN LAYOUT =========================
    ColumnLayout {
        id: mainColumn
        width: Math.min(parent.width - 64, 920)
        anchors.horizontalCenter: parent.horizontalCenter
        y: 28
        spacing: 22

        // ============== HERO HEADER ==============
        RowLayout {
            Layout.fillWidth: true
            spacing: 18

            Rectangle {
                width: 68
                height: 68
                radius: 20
                gradient: Gradient {
                    GradientStop { position: 0; color: Theme.accent }
                    GradientStop { position: 1; color: Theme.violet }
                }
                Text {
                    anchors.centerIn: parent
                    text: profileData.full_name && profileData.full_name.length > 0
                          ? profileData.full_name[0].toUpperCase()
                          : "U"
                    color: "white"
                    font.pixelSize: 28
                    font.weight: Font.Bold
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3
                Text {
                    text: "Settings & System Control"
                    color: Theme.text
                    font.pixelSize: 24
                    font.weight: Font.Bold
                    font.letterSpacing: -0.5
                }
                Text {
                    text: String(profileData.email || (backend ? backend.userEmail : "") || "Local Clinical Node")
                    color: Theme.muted
                    font.pixelSize: 12
                }
                Text {
                    text: "Configure clinical equations, local AI, vision digitizer and offline security."
                    color: Theme.muted
                    font.pixelSize: 11
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
            }

            Item { Layout.fillWidth: true }

            HgButton {
                visible: root.currentCategoryIndex === 0 || root.currentCategoryIndex === 1
                text: isDirty ? "Save changes" : "All saved"
                primary: true
                enabled: (root.currentCategoryIndex === 0) ? (isDirty && birthDateValid) : isDirty
                onClicked: saveAll()
            }
        }

        // ============== CATEGORY NAVIGATION TABS ==============
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: [
                    { id: 0, title: "Clinical Profile", icon: "🩺", desc: "Biometrics & Vitals" },
                    { id: 1, title: "AI & Vision OCR", icon: "🤖", desc: "LLM & Digitizer" },
                    { id: 2, title: "License & Node", icon: "🛡️", desc: "Hardware Binding" },
                    { id: 3, title: "System & About", icon: "⚙️", desc: "Theme & Runtime" }
                ]

                delegate: Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 52
                    radius: 12
                    color: root.currentCategoryIndex === modelData.id
                           ? (Theme.dark ? "#262244" : "#EEECFB")
                           : (tabHover.hovered ? Theme.surfaceAlt : Theme.surface)
                    border.color: root.currentCategoryIndex === modelData.id ? Theme.violet : Theme.border
                    border.width: root.currentCategoryIndex === modelData.id ? 1.5 : 1

                    Behavior on color { ColorAnimation { duration: 120 } }
                    Behavior on border.color { ColorAnimation { duration: 120 } }

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 8

                        Text {
                            text: modelData.icon
                            font.pixelSize: 16
                        }

                        ColumnLayout {
                            spacing: 1
                            Text {
                                text: modelData.title
                                font.pixelSize: 12
                                font.weight: root.currentCategoryIndex === modelData.id ? Font.Bold : Font.DemiBold
                                color: root.currentCategoryIndex === modelData.id ? Theme.violet : Theme.text
                            }
                            Text {
                                text: modelData.desc
                                font.pixelSize: 9
                                color: Theme.muted
                            }
                        }
                    }

                    MouseArea {
                        id: tabHover
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.currentCategoryIndex = modelData.id
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Theme.border
            opacity: 0.5
        }

        // =================================================================
        // TAB 0: CLINICAL PROFILE & BIOMETRICS
        // =================================================================
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 20
            visible: root.currentCategoryIndex === 0

            // SECTION 1: PERSONAL IDENTITY
            SettingsSection {
                title: "PERSONAL IDENTITY"
                subtitle: "Clinician identity and account profile"
                icon: "👤"

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 16
                    rowSpacing: 14

                    SettingsField {
                        label: "Full name"
                        placeholder: "e.g. Dr. Ehsan Bahrami"
                        textValue: String(profileData.full_name || "")
                        onTextChanged: function(newValue) {
                            profileData.full_name = newValue
                            checkDirty()
                        }
                    }

                    SettingsField {
                        label: "Email address"
                        placeholder: "name@example.com"
                        textValue: String(profileData.email || (backend ? backend.userEmail : "") || "")
                        readOnly: true
                        hint: "Bound to local account profile"
                    }
                }
            }

            // SECTION 2: CLINICAL PROFILE
            SettingsSection {
                title: "CLINICAL PROFILE"
                subtitle: "Biometrics used by CKD-EPI, KDIGO 2024, ASCVD and SCORE2 equations"
                icon: "🧬"

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 14

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 16
                        rowSpacing: 14

                        SettingsField {
                            label: "Birth date"
                            placeholder: "YYYY-MM-DD"
                            textValue: String(profileData.birth_date || "")
                            valid: birthDateValid
                            validationError: "Valid format: YYYY-MM-DD (1900–2026)"
                            hint: "Required for age-calibrated models"
                            onTextChanged: function(newValue) {
                                profileData.birth_date = newValue
                                checkDirty()
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Text {
                                text: "Calculated age"
                                color: Theme.muted
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 44
                                radius: 11
                                color: Theme.surfaceAlt
                                border.color: Theme.border
                                Text {
                                    anchors.centerIn: parent
                                    text: computedAge > 0 ? (computedAge + " years old") : "—"
                                    color: computedAge > 0 ? Theme.accent : Theme.muted
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
                                }
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Text {
                            text: "Biological sex"
                            color: Theme.muted
                            font.pixelSize: 11
                            font.weight: Font.DemiBold
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            Repeater {
                                model: ["Female", "Male"]
                                delegate: Rectangle {
                                    Layout.fillWidth: true
                                    height: 44
                                    radius: 11
                                    color: profileData.sex === modelData
                                           ? (Theme.dark ? "#1A3655" : "#EFF6FF")
                                           : Theme.surface
                                    border.color: profileData.sex === modelData ? Theme.accent : Theme.border
                                    border.width: profileData.sex === modelData ? 1.5 : 1

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            profileData.sex = modelData
                                            checkDirty()
                                        }
                                    }

                                    RowLayout {
                                        anchors.centerIn: parent
                                        spacing: 6
                                        Text {
                                            text: modelData === "Female" ? "♀" : "♂"
                                            color: profileData.sex === modelData ? Theme.accent : Theme.muted
                                            font.pixelSize: 16
                                        }
                                        Text {
                                            text: modelData
                                            color: profileData.sex === modelData ? Theme.accent : Theme.text
                                            font.pixelSize: 13
                                            font.weight: Font.DemiBold
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border; opacity: 0.4 }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 16
                        rowSpacing: 14

                        SettingsField {
                            label: "Weight (kg)"
                            placeholder: "e.g. 72.5"
                            textValue: profileData.weight ? String(profileData.weight) : ""
                            validator: DoubleValidator { bottom: 20; top: 300; decimals: 1 }
                            onTextChanged: function(newValue) {
                                profileData.weight = newValue ? parseFloat(newValue) : null
                                checkDirty()
                            }
                        }

                        SettingsField {
                            label: "Height (cm)"
                            placeholder: "e.g. 175"
                            textValue: profileData.height ? String(profileData.height) : ""
                            validator: IntValidator { bottom: 50; top: 250 }
                            onTextChanged: function(newValue) {
                                profileData.height = newValue ? parseInt(newValue) : null
                                checkDirty()
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Text {
                                text: "Calculated BMI"
                                color: Theme.muted
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 44
                                radius: 11
                                color: Theme.surfaceAlt
                                border.color: Theme.border
                                RowLayout {
                                    anchors.centerIn: parent
                                    spacing: 8
                                    Text {
                                        text: computedBMI > 0 ? computedBMI.toFixed(1) : "—"
                                        color: bmiColor
                                        font.pixelSize: 14
                                        font.bold: true
                                    }
                                    Rectangle {
                                        visible: computedBMI > 0
                                        implicitWidth: bmiTag.implicitWidth + 12
                                        height: 20
                                        radius: 6
                                        color: bmiColor
                                        opacity: 0.15
                                    }
                                    Text {
                                        id: bmiTag
                                        visible: computedBMI > 0
                                        text: bmiCategory
                                        color: bmiColor
                                        font.pixelSize: 10
                                        font.bold: true
                                    }
                                }
                            }
                        }

                        SettingsField {
                            label: "Waist (cm)"
                            placeholder: "e.g. 88"
                            textValue: profileData.waist ? String(profileData.waist) : ""
                            hint: "Used by FINDRISC model"
                            validator: IntValidator { bottom: 40; top: 200 }
                            onTextChanged: function(newValue) {
                                profileData.waist = newValue ? parseInt(newValue) : null
                                checkDirty()
                            }
                        }
                    }
                }
            }

            // SECTION 3: VITAL SIGNS
            SettingsSection {
                title: "VITAL SIGNS"
                subtitle: "Baseline parameters for cardiovascular risk evaluation"
                icon: "❤️"

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 16
                    rowSpacing: 14

                    SettingsField {
                        label: "Systolic BP (mmHg)"
                        placeholder: "e.g. 120"
                        textValue: profileData.systolic_bp ? String(profileData.systolic_bp) : ""
                        validator: IntValidator { bottom: 60; top: 260 }
                        onTextChanged: function(newValue) {
                            profileData.systolic_bp = newValue ? parseInt(newValue) : null
                            checkDirty()
                        }
                    }

                    SettingsField {
                        label: "Diastolic BP (mmHg)"
                        placeholder: "e.g. 80"
                        textValue: profileData.diastolic_bp ? String(profileData.diastolic_bp) : ""
                        validator: IntValidator { bottom: 40; top: 160 }
                        onTextChanged: function(newValue) {
                            profileData.diastolic_bp = newValue ? parseInt(newValue) : null
                            checkDirty()
                        }
                    }

                    SettingsField {
                        label: "Heart rate (bpm)"
                        placeholder: "e.g. 72"
                        textValue: profileData.heart_rate ? String(profileData.heart_rate) : ""
                        validator: IntValidator { bottom: 30; top: 220 }
                        onTextChanged: function(newValue) {
                            profileData.heart_rate = newValue ? parseInt(newValue) : null
                            checkDirty()
                        }
                    }

                    SettingsField {
                        label: "Sleep duration (hrs)"
                        placeholder: "e.g. 7"
                        textValue: profileData.sleep_hours ? String(profileData.sleep_hours) : ""
                        validator: DoubleValidator { bottom: 0; top: 24; decimals: 1 }
                        onTextChanged: function(newValue) {
                            profileData.sleep_hours = newValue ? parseFloat(newValue) : null
                            checkDirty()
                        }
                    }
                }
            }

            // SECTION 4: LIFESTYLE & RISK FACTORS
            SettingsSection {
                title: "LIFESTYLE & RISK FACTORS"
                subtitle: "Used by FINDRISC, ASCVD-PCE, SCORE2 and diabetes risk screening"
                icon: "🧭"

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14

                    SettingsToggle {
                        text: "Smoking"
                        description: "Current tobacco smoking habit"
                        icon: "🚬"
                        checked: profileData.smoking
                        Layout.fillWidth: true
                        onToggled: {
                            profileData.smoking = !profileData.smoking
                            checkDirty()
                        }
                    }

                    SettingsToggle {
                        text: "Physical activity"
                        description: "At least 30 min of moderate exercise daily"
                        icon: "🏃"
                        checked: profileData.physical_activity
                        Layout.fillWidth: true
                        onToggled: {
                            profileData.physical_activity = !profileData.physical_activity
                            checkDirty()
                        }
                    }
                }
            }

            // SECTION 5: FAMILY HISTORY
            SettingsSection {
                title: "FAMILY HISTORY"
                subtitle: "First-degree biological relatives (parents, siblings, children)"
                icon: "👪"

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14

                    SettingsToggle {
                        text: "Diabetes"
                        description: "Family history of Type 1 or Type 2 DM"
                        icon: "🩸"
                        checked: profileData.family_history_dm
                        Layout.fillWidth: true
                        onToggled: {
                            profileData.family_history_dm = !profileData.family_history_dm
                            checkDirty()
                        }
                    }

                    SettingsToggle {
                        text: "Heart disease"
                        description: "Premature CAD / Myocardial Infarction"
                        icon: "❤️"
                        checked: profileData.family_history_cad
                        Layout.fillWidth: true
                        onToggled: {
                            profileData.family_history_cad = !profileData.family_history_cad
                            checkDirty()
                        }
                    }

                    SettingsToggle {
                        text: "Hypertension"
                        description: "Family history of chronic high BP"
                        icon: "📈"
                        checked: profileData.family_history_htn
                        Layout.fillWidth: true
                        onToggled: {
                            profileData.family_history_htn = !profileData.family_history_htn
                            checkDirty()
                        }
                    }
                }
            }

            // BOTTOM PROFILE SAVE BAR
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                HgButton {
                    text: "Discard changes"
                    enabled: isDirty
                    onClicked: {
                        loadProfile()
                        isDirty = false
                    }
                }

                Item { Layout.fillWidth: true }

                Text {
                    visible: isDirty
                    text: "● Unsaved profile changes"
                    color: Theme.warning
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                }

                HgButton {
                    text: "Save profile"
                    primary: true
                    enabled: isDirty && birthDateValid
                    onClicked: saveAll()
                }
            }
        }

        // =================================================================
        // TAB 1: AI & VISION OCR ENGINE
        // =================================================================
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 20
            visible: root.currentCategoryIndex === 1

            // SECTION 6: AI ASSISTANT PREFERENCES
            SettingsSection {
                title: "AI ASSISTANT PREFERENCES"
                subtitle: "Configure the local clinical explanation chat engine (100% On-Device / Scheduled for next update)"
                icon: "💬"

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 14

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 38
                        radius: 10
                        color: Theme.dark ? "#172554" : "#EFF6FF"
                        border.color: Theme.dark ? "#1E40AF" : "#BFDBFE"
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8
                            Text { text: "ℹ️"; font.pixelSize: 12 }
                            Text {
                                text: "Local Chatbot Engine is under active development for the next update. Vision OCR and all diagnostic engines are fully active."
                                color: Theme.dark ? "#93C5FD" : "#1D4ED8"
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 14

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Text {
                                text: "Conversation language"
                                color: Theme.muted
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                            }
                            ComboBox {
                                id: langBox
                                Layout.fillWidth: true
                                implicitHeight: 44
                                model: ["English", "فارسی"]
                                currentIndex: backend ? (backend.chatLanguage === "fa" ? 1 : 0) : 0
                                onActivated: function(index) {
                                    if (backend) backend.chatSetLanguage(index === 1 ? "fa" : "en")
                                }
                                background: Rectangle {
                                    radius: 11
                                    color: langBox.pressed || langBox.hovered ? Theme.surfaceAlt : Theme.surface
                                    border.color: langBox.activeFocus ? Theme.accent : Theme.border
                                    border.width: langBox.activeFocus ? 1.5 : 1
                                    Behavior on border.color { ColorAnimation { duration: 140 } }
                                }
                                contentItem: Text {
                                    text: langBox.displayText
                                    color: Theme.text
                                    font.pixelSize: 13
                                    verticalAlignment: Text.AlignVCenter
                                    leftPadding: 14
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Text {
                                text: "Local Model Architecture (CPU Velocity Profile)"
                                color: Theme.muted
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                            }
                            ComboBox {
                                id: modelBox
                                Layout.fillWidth: true
                                implicitHeight: 44
                                model: [
                                    "qwen2.5:1.5b (⚡ Fastest & Recommended for CPU)",
                                    "qwen3:1.7b (⚡ Fast Lightweight Model)",
                                    "qwen2.5:0.5b (🚀 Ultra Fast — Lowest RAM)",
                                    "qwen3:4b (High Precision — Requires more RAM)",
                                    "qwen2.5:3b-instruct"
                                ]
                                property var modelKeys: ["qwen2.5:1.5b", "qwen3:1.7b", "qwen2.5:0.5b", "qwen3:4b", "qwen2.5:3b-instruct"]
                                currentIndex: {
                                    var cur = (backend ? backend.chatModel : "") || ""
                                    for (var i = 0; i < modelKeys.length; i++) {
                                        if (cur.indexOf(modelKeys[i]) !== -1) return i
                                    }
                                    return 0
                                }
                                onActivated: function(index) {
                                    if (index >= 0 && index < modelKeys.length) {
                                        backend.chatSetModel(modelKeys[index])
                                    }
                                }
                                background: Rectangle {
                                    radius: 11
                                    color: modelBox.pressed || modelBox.hovered ? Theme.surfaceAlt : Theme.surface
                                    border.color: modelBox.activeFocus ? Theme.accent : Theme.border
                                    border.width: modelBox.activeFocus ? 1.5 : 1
                                    Behavior on border.color { ColorAnimation { duration: 140 } }
                                }
                                contentItem: Text {
                                    text: modelBox.displayText
                                    color: Theme.text
                                    font.pixelSize: 13
                                    verticalAlignment: Text.AlignVCenter
                                    leftPadding: 14
                                }
                            }
                        }
                    }

                    SettingsToggle {
                        text: "Auto-save clinical conversations"
                        description: "Chat history is saved locally in encrypted SQLite for temporal audit"
                        icon: "💾"
                        checked: true
                        onToggled: {}
                        Layout.fillWidth: true
                    }
                }
            }

            // SECTION 6.5: VISION OCR & LAB IMAGE DIGITIZER
            SettingsSection {
                title: "VISION OCR & LAB IMAGE DIGITIZER"
                subtitle: "Digitize laboratory photos and scanned PDFs into structured tables"
                icon: "📷"

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Text {
                        Layout.fillWidth: true
                        text: "Enter your Groq API Key (free at console.groq.com) to automatically digitize complex blood test tables with Llama-3.2-Vision. The model is optimized to 950 max tokens to avoid rate limits."
                        color: Theme.muted
                        font.pixelSize: 12
                        wrapMode: Text.Wrap
                        lineHeight: 1.3
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        TextField {
                            id: visionKeyField
                            Layout.fillWidth: true
                            implicitHeight: 44
                            placeholderText: "Enter Groq API Key (starts with gsk_...)"
                            text: (backend && backend.ocrApiKey) ? backend.ocrApiKey : ""
                            echoMode: showVisionKeyBtn.checked ? TextInput.Normal : TextInput.Password
                            horizontalAlignment: TextInput.AlignLeft
                            verticalAlignment: TextInput.AlignVCenter
                            font.family: "monospace"
                            font.pixelSize: 13
                            leftPadding: 14
                            rightPadding: 14
                            color: Theme.text
                            placeholderTextColor: Theme.muted
                            background: Rectangle {
                                radius: 11
                                color: Theme.surface
                                border.color: visionKeyField.activeFocus ? Theme.accent : Theme.border
                                border.width: visionKeyField.activeFocus ? 1.5 : 1
                            }
                            onTextChanged: checkDirty()
                            onEditingFinished: {
                                var k = visionKeyField.text.trim()
                                if (backend && k !== (backend.ocrApiKey || "").trim()) {
                                    backend.setOcrApiKey(k)
                                    checkDirty()
                                    backend.toast("success", k.length > 0 ? "Groq API Key saved successfully!" : "Groq API Key cleared.")
                                }
                            }
                            onAccepted: {
                                var k = visionKeyField.text.trim()
                                backend.setOcrApiKey(k)
                                checkDirty()
                                backend.toast("success", k.length > 0 ? "Groq API Key saved successfully!" : "Groq API Key cleared.")
                            }
                        }

                        ToolButton {
                            id: showVisionKeyBtn
                            checkable: true
                            implicitHeight: 44
                            implicitWidth: 44
                            text: checked ? "👁️" : "🔒"
                            ToolTip.visible: hovered
                            ToolTip.text: checked ? "Hide Secret API Key" : "Reveal Secret API Key"
                            contentItem: Text {
                                text: showVisionKeyBtn.text
                                font.pixelSize: 16
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle {
                                radius: 10
                                color: showVisionKeyBtn.hovered ? Theme.surfaceAlt : "transparent"
                                border.color: Theme.border
                            }
                        }

                        HgButton {
                            text: "📋 Copy"
                            implicitHeight: 44
                            enabled: visionKeyField.text.length > 0
                            onClicked: {
                                backend.copyText(visionKeyField.text)
                                backend.toast("info", "API Key copied to clipboard")
                            }
                        }

                        HgButton {
                            text: "💾 Save Key"
                            primary: true
                            implicitHeight: 44
                            onClicked: {
                                var k = visionKeyField.text.trim()
                                backend.setOcrApiKey(k)
                                checkDirty()
                                backend.toast("success", k.length > 0 ? "Groq API Key saved successfully!" : "Groq API Key cleared.")
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 14

                        Rectangle {
                            width: 10
                            height: 10
                            radius: 5
                            color: Boolean(backend && backend.ocrApiKey && backend.ocrApiKey.length > 5) ? Theme.success : Theme.warning
                        }

                        Text {
                            text: Boolean(backend && backend.ocrApiKey && backend.ocrApiKey.length > 5)
                                  ? "Active Engine: Cloud Vision AI (Llama-3.2-11B-Vision / High Precision)"
                                  : "Active Engine: Local Tesseract OCR (or text report parser)"
                            color: Theme.text
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                        }

                        Item { Layout.fillWidth: true }

                        Text {
                            visible: visionKeyField.text.trim() !== ((backend ? backend.ocrApiKey : "") || "").trim()
                            text: "⚠️ Unsaved changes — Click 'Save Key' or press Enter"
                            color: Theme.warning
                            font.pixelSize: 11
                            font.bold: true
                        }

                        Text {
                            visible: visionKeyField.text.trim() === ((backend ? backend.ocrApiKey : "") || "").trim() && Boolean(backend && backend.ocrApiKey && backend.ocrApiKey.length > 5)
                            text: "✓ Saved & Persistent"
                            color: Theme.success
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }
                }
            }
        }

        // =================================================================
        // TAB 2: HARDWARE LICENSE & SECURITY
        // =================================================================
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 20
            visible: root.currentCategoryIndex === 2

            // SECTION 8.5: OFFLINE CRYPTOGRAPHIC LICENSE
            SettingsSection {
                title: "OFFLINE CRYPTOGRAPHIC LICENSE"
                subtitle: "Node-locked digital certificate & anti-tamper security"
                icon: "🛡️"

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 14

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: midCol.implicitHeight + 20
                            radius: 10
                            color: Theme.surfaceAlt
                            border.color: Theme.border

                            ColumnLayout {
                                id: midCol
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 4

                                Text {
                                    text: "Hardware Machine ID (Locked Node)"
                                    color: Theme.muted
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                }

                                Text {
                                    text: (backend ? backend.licenseMachineId : "") || "Probing Hardware ID..."
                                    color: Theme.accent
                                    font.pixelSize: 13
                                    font.bold: true
                                    font.family: "monospace"
                                }
                            }
                        }

                        HgButton {
                            text: "📋 Copy ID"
                            Layout.preferredHeight: 46
                            onClicked: {
                                backend.copyMachineId()
                                backend.toast("info", "Machine ID copied to clipboard")
                            }
                        }
                    }

                    // License Input Row with Eye Reveal, File Picker, and Activation
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        TextField {
                            id: updateKeyField
                            Layout.fillWidth: true
                            implicitHeight: 44
                            placeholderText: "Enter updated license key (HGLIC-...)"
                            horizontalAlignment: TextInput.AlignLeft
                            verticalAlignment: TextInput.AlignVCenter
                            font.family: "monospace"
                            font.pixelSize: 12
                            echoMode: showLicenseBtn.checked ? TextInput.Normal : TextInput.Password
                            leftPadding: 14
                            rightPadding: 14
                            color: Theme.text
                            placeholderTextColor: Theme.muted
                            background: Rectangle {
                                radius: 11
                                color: Theme.surface
                                border.color: updateKeyField.activeFocus ? Theme.accent : Theme.border
                                border.width: updateKeyField.activeFocus ? 1.5 : 1
                            }
                        }

                        ToolButton {
                            id: showLicenseBtn
                            checkable: true
                            implicitHeight: 44
                            implicitWidth: 44
                            text: checked ? "👁️" : "🔒"
                            ToolTip.visible: hovered
                            ToolTip.text: checked ? "Hide License Characters" : "Reveal License Characters"
                            contentItem: Text {
                                text: showLicenseBtn.text
                                font.pixelSize: 16
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle {
                                radius: 10
                                color: showLicenseBtn.hovered ? Theme.surfaceAlt : "transparent"
                                border.color: Theme.border
                            }
                        }

                        HgButton {
                            text: "📋 Copy"
                            implicitHeight: 44
                            enabled: updateKeyField.text.length > 0 || (backend && backend.licenseValid)
                            onClicked: {
                                var val = updateKeyField.text.trim() || (backend.licenseMachineId ? "HGLIC-" + backend.licenseMachineId : "")
                                backend.copyText(val)
                                backend.toast("info", "License text copied to clipboard")
                            }
                        }

                        HgButton {
                            text: "📁 Load Key File"
                            implicitHeight: 44
                            onClicked: {
                                var content = backend.openLicenseFile()
                                if (content && content.length > 0) {
                                    updateKeyField.text = content.trim()
                                    backend.toast("info", "License certificate loaded from file.")
                                }
                            }
                        }

                        HgButton {
                            text: "Activate Key"
                            primary: true
                            implicitHeight: 44
                            enabled: updateKeyField.text.trim().length > 15
                            onClicked: {
                                var ok = backend.activateLicense(updateKeyField.text.trim())
                                if (ok) {
                                    backend.toast("success", "License renewed successfully!")
                                    updateKeyField.text = ""
                                } else {
                                    backend.toast("danger", backend.licenseError || "Invalid key")
                                }
                            }
                        }
                    }

                    // License Status and Re-check Row
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 20

                        RowLayout {
                            spacing: 8
                            Rectangle {
                                width: 10; height: 10; radius: 5
                                color: (backend && backend.licenseValid) ? Theme.success : Theme.danger
                            }
                            Text {
                                text: "Status: " + ((backend && backend.licenseValid) ? "ACTIVE (" + ((backend && backend.licenseTier) || "Standard") + ")" : "UNLICENSED / EXPIRED")
                                color: (backend && backend.licenseValid) ? Theme.success : Theme.danger
                                font.pixelSize: 12
                                font.bold: true
                            }
                        }

                        Text {
                            visible: Boolean(backend && backend.licenseCustomer)
                            text: "Licensed to: " + ((backend && backend.licenseCustomer) || "")
                            color: Theme.text
                            font.pixelSize: 12
                        }

                        Text {
                            visible: Boolean(backend && backend.licenseExpiry)
                            text: "Validity: " + ((backend && backend.licenseExpiry) || "")
                            color: Theme.muted
                            font.pixelSize: 12
                        }

                        Text {
                            visible: Boolean(backend && backend.licenseValid)
                            text: "🛡️ " + ((backend && backend.licenseAlgorithm) || "RSA-4096 / SHA-512")
                            color: Theme.accent
                            font.pixelSize: 11
                            font.bold: true
                        }

                        Item { Layout.fillWidth: true }

                        HgButton {
                            text: "🔄 Reactivate / Sync License"
                            implicitHeight: 36
                            onClicked: {
                                var ok = backend.checkLicense()
                                if (ok) {
                                    backend.toast("success", "Node license verified & ACTIVE!")
                                } else {
                                    backend.toast("warning", "License check: " + (backend.licenseError || "Unlicensed"))
                                }
                            }
                        }
                    }
                }
            }
        }

        // =================================================================
        // TAB 3: SYSTEM, THEME & ABOUT
        // =================================================================
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 20
            visible: root.currentCategoryIndex === 3

            // SECTION 7: APPEARANCE
            SettingsSection {
                title: "APPEARANCE"
                subtitle: "Interface theme and visual contrast preferences"
                icon: "🎨"

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    ThemeOptionCard {
                        text: "Light"
                        icon: "☀️"
                        active: !Theme.dark
                        Layout.fillWidth: true
                        onClicked: Theme.dark = false
                    }

                    ThemeOptionCard {
                        text: "Dark"
                        icon: "🌙"
                        active: Theme.dark
                        Layout.fillWidth: true
                        onClicked: Theme.dark = true
                    }

                    ThemeOptionCard {
                        text: "System"
                        icon: "💻"
                        active: false
                        enabled: false
                        Layout.fillWidth: true
                    }
                }
            }

            // SECTION 8: SYSTEM STATUS
            SettingsSection {
                title: "SYSTEM STATUS"
                subtitle: "Live health and diagnostics of the HEMOGLYPH runtime"
                icon: "⚙️"

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: statusGrid.implicitHeight + 28
                        radius: 14
                        color: Theme.surfaceAlt
                        border.color: Theme.border

                        GridLayout {
                            id: statusGrid
                            anchors.fill: parent
                            anchors.margins: 14
                            columns: 2
                            columnSpacing: 20
                            rowSpacing: 10

                            Repeater {
                                model: buildStatusRows()
                                delegate: RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10

                                    Rectangle {
                                        width: 10
                                        height: 10
                                        radius: 5
                                        color: model.isDev ? "#38BDF8" : (model.ok ? Theme.success : Theme.danger)
                                    }
                                    Text {
                                        text: String(model.label || "")
                                        color: Theme.text
                                        font.pixelSize: 12
                                        font.weight: Font.DemiBold
                                        Layout.fillWidth: true
                                    }
                                    Text {
                                        text: String(model.value || "")
                                        color: Theme.muted
                                        font.pixelSize: 11
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: disclaimerRow.implicitHeight + 16
                        radius: 10
                        color: "#FFFBEB"
                        border.color: "#FDE68A"

                        RowLayout {
                            id: disclaimerRow
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8
                            Text { text: "⚠️"; font.pixelSize: 16; color: "#B54708" }
                            Text {
                                Layout.fillWidth: true
                                text: "Research Mode — Clinical algorithms require validation by a licensed medical practitioner before therapy."
                                color: "#8A6100"
                                font.pixelSize: 11
                                wrapMode: Text.Wrap
                            }
                        }
                    }
                }
            }

            // SECTION 9: DATA & PRIVACY
            SettingsSection {
                title: "DATA & PRIVACY"
                subtitle: "Your clinical data stays on this device by default"
                icon: "🔒"

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    SettingsActionRow {
                        icon: "📤"
                        title: "Export all analyses"
                        subtitle: "Download a structured JSON backup of your saved patient tests"
                        actionText: "Export"
                        onTriggered: backend.toast("info", "Export feature coming soon.")
                    }

                    SettingsActionRow {
                        icon: "🗑️"
                        title: "Clear chat history"
                        subtitle: "Remove all saved local AI conversations from database"
                        actionText: "Clear"
                        danger: true
                        onTriggered: backend.toast("warning", "This action cannot be undone.")
                    }

                    SettingsActionRow {
                        icon: "🚪"
                        title: "Sign out"
                        subtitle: "Exit current session and return to authentication screen"
                        actionText: "Sign out"
                        danger: true
                        onTriggered: backend.logout()
                    }
                }
            }

            // SECTION 10: ABOUT HEMOGLYPH
            SettingsSection {
                title: "ABOUT HEMOGLYPH"
                subtitle: "Next-generation laboratory decision-support platform"
                icon: "🧬"

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 14
                        rowSpacing: 8

                        Text { text: "Application"; color: Theme.muted; font.pixelSize: 11 }
                        Text { text: "HEMOGLYPH " + String((backend && backend.appBuild) || "1.3.1"); color: Theme.text; font.pixelSize: 12; font.family: "monospace" }
                        Text { text: "Analysis schema"; color: Theme.muted; font.pixelSize: 11 }
                        Text { text: "2.0.0-clinical"; color: Theme.text; font.pixelSize: 12; font.family: "monospace" }
                        Text { text: "Feature registry"; color: Theme.muted; font.pixelSize: 11 }
                        Text { text: String((backend && backend.featureCount) || 0) + " canonical features"; color: Theme.text; font.pixelSize: 12 }
                        Text { text: "Disease registry"; color: Theme.muted; font.pixelSize: 11 }
                        Text { text: String((backend && backend.diseaseCount) || 0) + " concepts · " + String((backend && backend.ruleCount) || 0) + " rules"; color: Theme.text; font.pixelSize: 12 }
                        Text { text: "Prediction engine"; color: Theme.muted; font.pixelSize: 11 }
                        Text { text: "100 validated multi-system models"; color: Theme.text; font.pixelSize: 12 }
                        Text { text: "OCR backend"; color: Theme.muted; font.pixelSize: 11 }
                        Text {
                            text: (backend && backend.ocrError && backend.ocrError.length) ? "Not available" : "Ready"
                            color: (backend && backend.ocrError && backend.ocrError.length) ? Theme.danger : Theme.success
                            font.pixelSize: 12
                        }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border; opacity: 0.4 }

                    Text {
                        Layout.fillWidth: true
                        text: "HEMOGLYPH is a specialized clinical decision-support tool. It computes validated scientific risk equations and identifies guideline-based patterns — it does not replace the professional clinical judgment of a licensed physician."
                        color: Theme.muted
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                        lineHeight: 1.4
                    }
                }
            }

            // SECTION 10.5: DEVELOPER CONTACT & CLINICAL INQUIRIES
            SettingsSection {
                title: "DEVELOPER CONTACT & SUPPORT"
                subtitle: "Direct communication for clinical research, enterprise licensing, feedback and inquiries"
                icon: "✉️"

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: contactCol.implicitHeight + 20
                            radius: 12
                            color: Theme.surfaceAlt
                            border.color: Theme.border

                            ColumnLayout {
                                id: contactCol
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 4

                                Text {
                                    text: "Lead Architect & Developer: Sobhan Bahrami"
                                    color: Theme.text
                                    font.pixelSize: 13
                                    font.bold: true
                                }

                                Text {
                                    text: "sobahramisamani@gmail.com"
                                    color: Theme.accent
                                    font.pixelSize: 13
                                    font.bold: true
                                    font.family: "monospace"
                                }
                            }
                        }

                        HgButton {
                            text: "📧 Send Email"
                            primary: true
                            Layout.preferredHeight: 46
                            onClicked: Qt.openUrlExternally("mailto:sobahramisamani@gmail.com?subject=HEMOGLYPH%20Clinical%20Inquiry")
                        }

                        HgButton {
                            text: "📋 Copy"
                            Layout.preferredHeight: 46
                            onClicked: {
                                if (backend) {
                                    backend.copyText("sobahramisamani@gmail.com")
                                    backend.toast("info", "Email copied: sobahramisamani@gmail.com")
                                }
                            }
                        }
                    }
                }
            }
        }

        Item { Layout.preferredHeight: 30 }
    }

    // ========================= FUNCTIONS =========================
    function checkDirty() {
        var profileDirty = JSON.stringify(profileData) !== JSON.stringify(originalData)
        var keyDirty = (typeof visionKeyField !== "undefined" && visionKeyField !== null)
            ? (visionKeyField.text.trim() !== (backend.ocrApiKey || "").trim())
            : false
        isDirty = profileDirty || keyDirty
    }

    function saveAll() {
        var data = {
            "full_name": profileData.full_name,
            "birth_date": profileData.birth_date,
            "sex": profileData.sex,
            "weight": profileData.weight,
            "height": profileData.height,
            "waist": profileData.waist,
            "systolic_bp": profileData.systolic_bp,
            "diastolic_bp": profileData.diastolic_bp,
            "heart_rate": profileData.heart_rate,
            "sleep_hours": profileData.sleep_hours,
            "smoking": profileData.smoking ? "Yes" : "No",
            "physical_activity": profileData.physical_activity ? "Active" : "Sedentary",
            "family_history_dm": profileData.family_history_dm ? "Yes" : "No",
            "family_history_cad": profileData.family_history_cad ? "Yes" : "No",
            "family_history_htn": profileData.family_history_htn ? "Yes" : "No"
        }
        if (backend) {
            if (backend.saveProfile) {
                backend.saveProfile(data)
            } else if (backend.saveStableProfile) {
                backend.saveStableProfile(data)
            }
            if (typeof visionKeyField !== "undefined" && visionKeyField !== null) {
                backend.setOcrApiKey(visionKeyField.text.trim())
            }
        }
        originalData = JSON.parse(JSON.stringify(profileData))
        checkDirty()
        backend.toast("success", "Settings saved successfully")
    }

    function loadProfile() {
        var p = backend.profile()
        profileData.full_name = String(p.full_name || "")
        profileData.email = String(p.email || backend.userEmail || "")
        profileData.birth_date = String(p.birth_date || "")
        profileData.sex = String(p.sex || "Female")
        profileData.weight = p.weight || null
        profileData.height = p.height || null
        profileData.waist = p.waist || null
        profileData.systolic_bp = p.systolic_bp || null
        profileData.diastolic_bp = p.diastolic_bp || null
        profileData.heart_rate = p.heart_rate || null
        profileData.sleep_hours = p.sleep_hours || null
        profileData.smoking = (p.smoking === "Yes")
        profileData.physical_activity = (p.physical_activity === "Active")
        profileData.family_history_dm = (p.family_history_dm === "Yes")
        profileData.family_history_cad = (p.family_history_cad === "Yes")
        profileData.family_history_htn = (p.family_history_htn === "Yes")
        if (typeof visionKeyField !== "undefined" && visionKeyField !== null) {
            visionKeyField.text = backend.ocrApiKey || ""
        }
        originalData = JSON.parse(JSON.stringify(profileData))
        isDirty = false
    }

    Connections {
        target: backend
        function onOcrApiKeyChanged() {
            if (typeof visionKeyField !== "undefined" && visionKeyField !== null) {
                if (visionKeyField.text.trim() !== (backend.ocrApiKey || "").trim()) {
                    visionKeyField.text = backend.ocrApiKey || ""
                    checkDirty()
                }
            }
        }
    }

    function buildStatusRows() {
        var hc = (backend && backend.healthcheck) ? backend.healthcheck() : null
        if (!hc) return []
        var licOk = Boolean(backend && backend.licenseValid)
        var licTier = (backend && backend.licenseTier) || "Standard"
        var hasOcrErr = Boolean(backend && backend.ocrError && backend.ocrError.length)
        return [
            { label: "Hardware license", value: licOk ? ("Valid (" + licTier + ")") : "Unlicensed", ok: licOk },
            { label: "Application", value: String(hc.app ? (hc.app.name + " " + hc.app.version) : ""), ok: true },
            { label: "AI assistant", value: "Under Development (Next Update)", ok: true, isDev: true },
            { label: "OCR engine", value: String(hc.ocr_backend || "unknown"), ok: !hasOcrErr },
            { label: "Analysis engine", value: String((hc.feature_count || 0) + " features"), ok: (hc.feature_count || 0) > 0 },
            { label: "Rule engine", value: String((hc.candidate_rule_count || 0) + " candidate rules"), ok: (hc.candidate_rule_count || 0) > 0 },
            { label: "Prediction engine", value: String(hc.prediction_engine || "legacy"), ok: true },
            { label: "Database", value: "SQLite (WAL)", ok: true }
        ]
    }

    Component.onCompleted: loadProfile()

    // =================================================================
    // SETTINGS SECTION COMPONENT (Explicit Card with Perfect Bounds)
    // =================================================================
    component SettingsSection: Rectangle {
        id: secCard
        property string title: ""
        property string subtitle: ""
        property string icon: ""
        default property alias content: contentLayout.children

        Layout.fillWidth: true
        implicitHeight: cardInnerLayout.implicitHeight + 44
        radius: 16
        color: Theme.surface
        border.color: Theme.border
        border.width: 1

        ColumnLayout {
            id: cardInnerLayout
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 22
            spacing: 16

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Rectangle {
                    width: 38
                    height: 38
                    radius: 11
                    color: Theme.surfaceAlt
                    border.color: Theme.border

                    Text {
                        anchors.centerIn: parent
                        text: secCard.icon
                        font.pixelSize: 18
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        text: secCard.title
                        color: Theme.text
                        font.pixelSize: 12
                        font.weight: Font.Bold
                        font.letterSpacing: 1.5
                    }
                    Text {
                        text: secCard.subtitle
                        color: Theme.muted
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.border
                opacity: 0.5
            }

            ColumnLayout {
                id: contentLayout
                Layout.fillWidth: true
                spacing: 14
            }
        }
    }

    // =================================================================
    // SETTINGS FIELD COMPONENT (Responsive Geometry with FillWidth)
    // =================================================================
    component SettingsField: ColumnLayout {
        id: fieldRoot
        
        property string label: ""
        property string placeholder: ""
        property string hint: ""
        property string textValue: ""
        property bool readOnly: false
        property color accentColor: Theme.text
        property bool valid: true
        property string validationError: ""
        property alias validator: internalField.validator
        
        signal textChanged(string newValue)

        Layout.fillWidth: true
        spacing: 6

        Text {
            text: fieldRoot.label
            color: Theme.muted
            font.pixelSize: 11
            font.weight: Font.DemiBold
            Layout.fillWidth: true
        }

        TextField {
            id: internalField
            Layout.fillWidth: true
            implicitHeight: 44
            placeholderText: fieldRoot.placeholder
            text: fieldRoot.textValue
            horizontalAlignment: TextInput.AlignLeft
            verticalAlignment: TextInput.AlignVCenter
            color: fieldRoot.readOnly ? fieldRoot.accentColor : Theme.text
            readOnly: fieldRoot.readOnly
            selectByMouse: true
            placeholderTextColor: Theme.muted
            
            onTextChanged: {
                if (!fieldRoot.readOnly) {
                    fieldRoot.textChanged(text)
                }
            }
            
            font.pixelSize: 13
            leftPadding: 14
            rightPadding: 14
            background: Rectangle {
                radius: 11
                color: fieldRoot.readOnly ? Theme.surfaceAlt : Theme.surface
                border.color: !fieldRoot.valid ? Theme.danger :
                              (internalField.activeFocus ? Theme.accent : Theme.border)
                border.width: internalField.activeFocus ? 1.5 : 1
                Behavior on border.color { ColorAnimation { duration: 140 } }
            }
        }

        Text {
            visible: !fieldRoot.valid && fieldRoot.validationError.length > 0
            text: fieldRoot.validationError
            color: Theme.danger
            font.pixelSize: 10
            font.italic: true
            Layout.fillWidth: true
        }

        Text {
            visible: fieldRoot.hint.length > 0 && fieldRoot.valid
            text: fieldRoot.hint
            color: Theme.muted
            font.pixelSize: 10
            font.italic: true
            Layout.fillWidth: true
        }
    }

    // =================================================================
    // SETTINGS TOGGLE COMPONENT
    // =================================================================
    component SettingsToggle: Rectangle {
        property string text: ""
        property string description: ""
        property string icon: ""
        property bool checked: false

        signal toggled()

        height: 76
        radius: 14
        color: checked ? (Theme.dark ? "#1A3655" : "#EFF6FF") : Theme.surfaceAlt
        border.color: checked ? Theme.accent : Theme.border
        border.width: checked ? 1.5 : 1

        Behavior on color { ColorAnimation { duration: 180 } }
        Behavior on border.color { ColorAnimation { duration: 180 } }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true
            onClicked: parent.toggled()
        }

        RowLayout {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 12

            Rectangle {
                width: 38
                height: 38
                radius: 11
                color: checked ? Theme.accent : Theme.surface
                border.color: Theme.border

                Text {
                    anchors.centerIn: parent
                    text: icon
                    font.pixelSize: 17
                    color: checked ? "white" : Theme.text
                }

                Behavior on color { ColorAnimation { duration: 180 } }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Text {
                    text: text
                    color: Theme.text
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                Text {
                    text: description
                    color: Theme.muted
                    font.pixelSize: 10
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
            }

            Rectangle {
                width: 44
                height: 24
                radius: 12
                color: checked ? Theme.accent : Theme.border

                Rectangle {
                    width: 18
                    height: 18
                    radius: 9
                    color: "white"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: checked ? parent.right : undefined
                    anchors.left: checked ? undefined : parent.left
                    anchors.rightMargin: 3
                    anchors.leftMargin: 3
                    Behavior on anchors.rightMargin { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                    Behavior on anchors.leftMargin { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                }

                Behavior on color { ColorAnimation { duration: 180 } }
            }
        }
    }

    // =================================================================
    // THEME OPTION CARD COMPONENT
    // =================================================================
    component ThemeOptionCard: Rectangle {
        property string text: ""
        property string icon: ""
        property bool active: false

        signal clicked()

        height: 84
        radius: 14
        color: active ? (Theme.dark ? "#1A3655" : "#EFF6FF") : Theme.surfaceAlt
        border.color: active ? Theme.accent : Theme.border
        border.width: active ? 2 : 1

        Behavior on color { ColorAnimation { duration: 180 } }
        Behavior on border.color { ColorAnimation { duration: 180 } }

        MouseArea {
            anchors.fill: parent
            cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
            hoverEnabled: enabled
            onClicked: parent.clicked()
        }

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 6

            Text {
                text: icon
                font.pixelSize: 22
                Layout.alignment: Qt.AlignHCenter
                opacity: enabled ? 1 : 0.4
            }

            Text {
                text: text
                color: active ? Theme.accent : Theme.text
                font.pixelSize: 12
                font.weight: Font.DemiBold
                Layout.alignment: Qt.AlignHCenter
                opacity: enabled ? 1 : 0.4
            }
        }
    }

    // =================================================================
    // SETTINGS ACTION ROW COMPONENT
    // =================================================================
    component SettingsActionRow: Rectangle {
        property string icon: ""
        property string title: ""
        property string subtitle: ""
        property string actionText: ""
        property bool danger: false

        signal triggered()

        height: 64
        radius: 12
        color: Theme.surfaceAlt
        border.color: Theme.border

        RowLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 12

            Rectangle {
                width: 38
                height: 38
                radius: 10
                color: danger ? "#FEF3F2" : Theme.surface
                border.color: danger ? "#FDA29B" : Theme.border

                Text {
                    anchors.centerIn: parent
                    text: icon
                    font.pixelSize: 16
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Text {
                    text: title
                    color: danger ? Theme.danger : Theme.text
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                }
                Text {
                    text: subtitle
                    color: Theme.muted
                    font.pixelSize: 10
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }

            HgButton {
                text: actionText
                danger: danger
                onClicked: parent.parent.triggered()
            }
        }
    }
}
