import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

// Opening a file is the first thing a clinician does with a new patient,
// so only the name is required. Everything else can be filled in later
// from the file page; blocking on a national id would just push people
// into typing rubbish to get past the form.
Item {
    id: root

    signal closed()
    signal created(int patientId)

    function reset() {
        nameField.text = ""
        recordField.text = ""
        nationalField.text = ""
        birthField.text = ""
        phoneField.text = ""
        sexBox.currentIndex = 0
        errorText.text = ""
    }

    onVisibleChanged: if (visible) { reset(); nameField.forceActiveFocus() }

    // Scrim: clicking outside dismisses, and swallows clicks so the list
    // underneath cannot be operated while the form is open.
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.45
        MouseArea { anchors.fill: parent; onClicked: root.closed() }
    }

    HgCard {
        anchors.centerIn: parent
        width: Math.min(560, parent.width - 48)
        height: body.implicitHeight + 48

        MouseArea { anchors.fill: parent }   // keep clicks inside the card

        ColumnLayout {
            id: body
            anchors.fill: parent
            anchors.margins: 24
            spacing: 16

            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: "New patient file"
                    color: Theme.text
                    font.pixelSize: 18
                    font.bold: true
                }
                Item { Layout.fillWidth: true }
                Text {
                    text: "✕"
                    color: Theme.muted
                    font.pixelSize: 15
                    MouseArea {
                        anchors.fill: parent
                        anchors.margins: -8
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.closed()
                    }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: 2
                columnSpacing: 14
                rowSpacing: 12

                Field {
                    id: nameField
                    Layout.columnSpan: 2
                    label: "Full name *"
                    placeholder: "Patient's name as it appears on the referral"
                }
                Field { id: recordField; label: "Record number"; placeholder: "optional" }
                Field { id: nationalField; label: "National id"; placeholder: "optional" }
                Field { id: birthField; label: "Date of birth"; placeholder: "YYYY-MM-DD" }

                ColumnLayout {
                    spacing: 4
                    Text { text: "Sex"; color: Theme.muted; font.pixelSize: 10 }
                    ComboBox {
                        id: sexBox
                        Layout.fillWidth: true
                        // Sex selects reference ranges and gates several
                        // risk models, so an untouched form must not
                        // silently assert one.
                        model: ["Select…", "Female", "Male"]
                    }
                }

                Field {
                    id: phoneField
                    Layout.columnSpan: 2
                    label: "Phone"
                    placeholder: "optional"
                }
            }

            Text {
                id: errorText
                Layout.fillWidth: true
                color: Theme.danger
                font.pixelSize: 11
                wrapMode: Text.WordWrap
                visible: text.length > 0
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Text {
                    text: "Only the name is required."
                    color: Theme.muted
                    font.pixelSize: 10
                }
                Item { Layout.fillWidth: true }
                HgButton {
                    text: "Cancel"
                    onClicked: root.closed()
                }
                HgButton {
                    text: "Create file"
                    onClicked: root.submit()
                }
            }
        }
    }

    function submit() {
        if (!nameField.text.trim().length) {
            errorText.text = "Enter the patient's name."
            nameField.forceActiveFocus()
            return
        }
        if (birthField.text.length &&
                !/^\d{4}-\d{2}-\d{2}$/.test(birthField.text.trim())) {
            errorText.text = "Date of birth must look like 1968-04-12."
            return
        }
        var sex = sexBox.currentIndex === 1 ? "female"
                : sexBox.currentIndex === 2 ? "male" : ""
        var id = backend.createPatient({
            "fullName":   nameField.text.trim(),
            "recordNo":   recordField.text.trim(),
            "nationalId": nationalField.text.trim(),
            "birthDate":  birthField.text.trim(),
            "phone":      phoneField.text.trim(),
            "sex":        sex
        })
        if (id > 0)
            root.created(id)
        else
            errorText.text = "Could not create the file."
    }

    component Field: ColumnLayout {
        property alias text: input.text
        property string label: ""
        property string placeholder: ""
        spacing: 4
        Text { text: parent.label; color: Theme.muted; font.pixelSize: 10 }
        Rectangle {
            Layout.fillWidth: true
            height: 36
            radius: 6
            color: Theme.surfaceAlt
            border.color: input.activeFocus ? Theme.accent : Theme.border
            TextInput {
                id: input
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                horizontalAlignment: TextInput.AlignLeft
                verticalAlignment: Text.AlignVCenter
                color: Theme.text
                font.pixelSize: 12
                clip: true
                selectByMouse: true
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    visible: !input.text.length && !input.activeFocus
                    text: parent.parent.parent.placeholder
                    color: Theme.muted
                    font.pixelSize: 12
                }
            }
        }
    }
}

