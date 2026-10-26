import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

// The archive is the clinician's way in. They know the patient's name,
// not a record id, so search is the primary control and the list below it
// is only a convenience for the files they touched most recently.
Item {
    id: root

    property bool showNewPatient: false

    Component.onCompleted: backend.searchPatients("")

    Connections {
        target: backend
        function onLoggedInChanged() { backend.searchPatients("") }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        // ---- header: new patient sits above search, as requested ----
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            ColumnLayout {
                spacing: 2
                Text {
                    text: "Patient archive"
                    color: Theme.text
                    font.pixelSize: 22
                    font.bold: true
                }
                Text {
                    text: (backend && backend.patientRows ? backend.patientRows.length : 0) + " file(s)"
                    color: Theme.muted
                    font.pixelSize: 11
                }
            }

            Item { Layout.fillWidth: true }

            HgButton {
                text: "+  New patient"
                onClicked: root.showNewPatient = true
            }
        }

        // ---- search ----
        Rectangle {
            Layout.fillWidth: true
            height: 44
            radius: 8
            color: Theme.surface
            border.color: searchField.activeFocus ? Theme.accent : Theme.border

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 10
                spacing: 8

                Text { text: "⌕"; color: Theme.muted; font.pixelSize: 17 }

                TextInput {
                    id: searchField
                    Layout.fillWidth: true
                    color: Theme.text
                    font.family: Theme.fontFamily
                    font.pixelSize: 13
                    horizontalAlignment: TextInput.AlignLeft
                    verticalAlignment: TextInput.AlignVCenter
                    clip: true
                    selectByMouse: true
                    // Search as they type: with a few hundred files the
                    // round trip is cheap and waiting for Enter feels dead.
                    onTextChanged: backend.searchPatients(text)

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: !searchField.text.length
                        text: "Search by name, record number, national id or phone"
                        color: Theme.muted
                        font.pixelSize: 13
                    }
                }

                Text {
                    visible: searchField.text.length > 0
                    text: "✕"
                    color: Theme.muted
                    font.pixelSize: 13
                    MouseArea {
                        anchors.fill: parent
                        anchors.margins: -6
                        cursorShape: Qt.PointingHandCursor
                        onClicked: searchField.text = ""
                    }
                }
            }
        }

        // ---- empty state ----
        HgCard {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !(backend && backend.patientRows && backend.patientRows.length > 0)

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 10
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: searchField.text.length ? "No match" : "No patient files yet"
                    color: Theme.text
                    font.pixelSize: 16
                    font.bold: true
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: searchField.text.length
                          ? "Nothing matches “" + searchField.text + "”."
                          : "Create a file before running an analysis."
                    color: Theme.muted
                    font.pixelSize: 12
                }
                HgButton {
                    Layout.alignment: Qt.AlignHCenter
                    visible: !searchField.text.length
                    text: "Create the first file"
                    onClicked: root.showNewPatient = true
                }
            }
        }

        // ---- results ----
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: Boolean(backend && backend.patientRows && backend.patientRows.length > 0)
            clip: true
            spacing: 8
            model: backend ? backend.patientRows : []
            ScrollBar.vertical: ScrollBar {}

            delegate: HgCard {
                width: ListView.view.width
                height: 78
                interactive: true

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        backend.openPatient(modelData.id)
                        backend.navigate("patientFile")
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    spacing: 14

                    // initial badge
                    Rectangle {
                        width: 40; height: 40; radius: 20
                        color: Theme.surfaceAlt
                        border.color: Theme.border
                        Text {
                            anchors.centerIn: parent
                            text: (modelData.fullName || "?").charAt(0).toUpperCase()
                            color: Theme.accent
                            font.pixelSize: 16
                            font.bold: true
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        Text {
                            text: modelData.fullName
                            color: Theme.text
                            font.pixelSize: 14
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: {
                                var bits = [modelData.recordNo]
                                if (modelData.sex) bits.push(modelData.sex)
                                if (modelData.birthDate) bits.push(modelData.birthDate)
                                if (modelData.nationalId) bits.push("ID " + modelData.nationalId)
                                return bits.join("  ·  ")
                            }
                            color: Theme.muted
                            font.pixelSize: 11
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }

                    ColumnLayout {
                        spacing: 3
                        Text {
                            Layout.alignment: Qt.AlignRight
                            text: modelData.visits + (modelData.visits === 1 ? " visit" : " visits")
                            color: modelData.visits ? Theme.accent : Theme.muted
                            font.pixelSize: 12
                            font.bold: true
                        }
                        Text {
                            Layout.alignment: Qt.AlignRight
                            text: modelData.lastVisit ? "last " + modelData.lastVisit : "no visits yet"
                            color: Theme.muted
                            font.pixelSize: 10
                        }
                    }

                    Text { text: "›"; color: Theme.muted; font.pixelSize: 20 }
                }
            }
        }
    }

    // ---- new patient dialog ----
    NewPatientDialog {
        id: newPatientDialog
        anchors.fill: parent
        visible: root.showNewPatient
        onClosed: root.showNewPatient = false
        onCreated: function(patientId) {
            root.showNewPatient = false
            backend.navigate("patientFile")
        }
    }
}

