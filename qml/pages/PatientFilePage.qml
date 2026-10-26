import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Item {
    id: root

    readonly property var patient: backend ? backend.activePatient : null

    // Two-step archive: the second click within five seconds commits.
    property bool confirmArchive: false
    Timer {
        id: archiveTimeout
        interval: 5000
        onTriggered: root.confirmArchive = false
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        // ---- Patient Identity Card ----
        HgCard {
            Layout.fillWidth: true
            implicitHeight: headerRow.implicitHeight + 36

            RowLayout {
                id: headerRow
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                spacing: 16

                Rectangle {
                    width: 56; height: 56; radius: 28
                    color: Theme.surfaceAlt
                    border.color: Theme.border
                    Text {
                        anchors.centerIn: parent
                        text: (root.patient.fullName || "?").charAt(0).toUpperCase()
                        color: Theme.accent
                        font.pixelSize: 22
                        font.bold: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    RowLayout {
                        spacing: 10
                        Text {
                            text: root.patient.fullName || "No Patient Selected"
                            color: Theme.text
                            font.pixelSize: 20
                            font.bold: true
                            elide: Text.ElideRight
                        }
                        Rectangle {
                            visible: (root.patient.recordNo || "").length > 0
                            implicitWidth: recChip.implicitWidth + 14
                            height: 22
                            radius: 11
                            color: Theme.surfaceAlt
                            border.color: Theme.border
                            Text {
                                id: recChip
                                anchors.centerIn: parent
                                text: root.patient.recordNo || ""
                                color: Theme.muted
                                font.pixelSize: 10
                                font.bold: true
                            }
                        }
                    }

                    RowLayout {
                        spacing: 8
                        Repeater {
                            model: {
                                var chips = []
                                if (root.patient.age) chips.push({ label: root.patient.age + " yrs", icon: "🎂" })
                                if (root.patient.sex) chips.push({ label: root.patient.sex, icon: "👤" })
                                if (root.patient.nationalId) chips.push({ label: "ID: " + root.patient.nationalId, icon: "🪪" })
                                if (root.patient.phone) chips.push({ label: root.patient.phone, icon: "📞" })
                                return chips
                            }
                            delegate: Rectangle {
                                height: 22
                                radius: 11
                                color: Theme.surfaceAlt
                                border.color: Theme.border
                                implicitWidth: chipRow.implicitWidth + 14
                                RowLayout {
                                    id: chipRow
                                    anchors.centerIn: parent
                                    spacing: 4
                                    Text { text: modelData.icon; font.pixelSize: 9 }
                                    Text {
                                        text: modelData.label
                                        color: Theme.muted
                                        font.pixelSize: 10
                                        font.bold: true
                                    }
                                }
                            }
                        }
                    }
                }

                RowLayout {
                    spacing: 8
                    Layout.alignment: Qt.AlignRight | Qt.AlignVCenter

                    HgButton {
                        text: "← Back to Archive"
                        onClicked: backend.navigate("archive")
                    }
                    HgButton {
                        text: confirmArchive ? "Confirm Archive?" : "Archive File"
                        danger: confirmArchive
                        onClicked: {
                            if (confirmArchive) {
                                backend.archivePatient(root.patient.id)
                                confirmArchive = false
                                backend.navigate("archive")
                            } else {
                                confirmArchive = true
                                archiveTimeout.restart()
                            }
                        }
                    }
                    HgButton {
                        text: "⚡ New Analysis for this Patient"
                        primary: true
                        onClicked: backend.navigate("newAnalysis")
                    }
                }
            }
        }

        // ---- Timeline Header ----
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Text {
                text: "Clinical Encounters & Longitudinal History"
                color: Theme.text
                font.pixelSize: 16
                font.bold: true
            }
            Rectangle {
                implicitWidth: countBadge.implicitWidth + 14
                height: 20
                radius: 10
                color: Theme.surfaceAlt
                border.color: Theme.border
                Text {
                    id: countBadge
                    anchors.centerIn: parent
                    text: (backend && backend.patientTimeline ? backend.patientTimeline.length : 0) + " recorded"
                    color: Theme.muted
                    font.pixelSize: 10
                    font.bold: true
                }
            }
            Item { Layout.fillWidth: true }
            Text {
                visible: Boolean(backend && backend.patientTimeline && backend.patientTimeline.length > 1)
                text: "📋 Encounters filed under this patient (each report is analysed as a single time point)"
                color: Theme.muted
                font.pixelSize: 11
            }
        }

        // ---- Empty State ----
        HgCard {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !(backend && backend.patientTimeline && backend.patientTimeline.length > 0)

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 12
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "🩺"
                    font.pixelSize: 42
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "No Recorded Encounters Yet"
                    color: Theme.text
                    font.pixelSize: 17
                    font.bold: true
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Run a clinical analysis to file the first encounter under this patient.\nEach visit is analysed independently in this release."
                    color: Theme.muted
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                }
                HgButton {
                    Layout.alignment: Qt.AlignHCenter
                    primary: true
                    text: "⚡ Start First Analysis"
                    onClicked: backend.navigate("newAnalysis")
                }
            }
        }

        // ---- Timeline ListView ----
        ListView {
            id: timelineList
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: Boolean(backend && backend.patientTimeline && backend.patientTimeline.length > 0)
            clip: true
            spacing: 12
            model: backend ? backend.patientTimeline : []
            ScrollBar.vertical: ScrollBar {}

            delegate: HgCard {
                id: encounterCard
                width: ListView.view.width
                implicitHeight: entryCol.implicitHeight + 28
                interactive: true

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (modelData.hasAnalysis || modelData.analysisId > 0) {
                            backend.openEncounter(modelData.id)
                        } else {
                            backend.loadEncounterToNewRun(modelData.id)
                        }
                    }
                }

                ColumnLayout {
                    id: entryCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 14
                    spacing: 10

                    // Top row: date, badge, action buttons
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Rectangle {
                            width: 10; height: 10; radius: 5
                            color: index === 0 ? Theme.accent : Theme.muted
                        }
                        Text {
                            text: modelData.date || "Recorded encounter"
                            color: Theme.text
                            font.pixelSize: 14
                            font.bold: true
                        }
                        Rectangle {
                            visible: index === 0
                            height: 20; radius: 10
                            implicitWidth: latestLabel.implicitWidth + 16
                            color: "#ECFDF3"
                            border.color: "#A6F0C5"
                            Text {
                                id: latestLabel
                                anchors.centerIn: parent
                                text: "★ Latest Encounter"
                                color: "#067647"
                                font.pixelSize: 9
                                font.bold: true
                            }
                        }

                        Item { Layout.fillWidth: true }

                        Rectangle {
                            height: 22; radius: 11
                            implicitWidth: labBadgeText.implicitWidth + 16
                            color: Theme.surfaceAlt
                            border.color: Theme.border
                            Text {
                                id: labBadgeText
                                anchors.centerIn: parent
                                text: modelData.labCount + " measurement(s)"
                                color: Theme.muted
                                font.pixelSize: 10
                                font.bold: true
                            }
                        }

                        // Direct Action Buttons
                        HgButton {
                            text: "📊 View Analysis"
                            primary: index === 0
                            onClicked: backend.openEncounter(modelData.id)
                        }
                        HgButton {
                            text: "⚡ Load Labs"
                            onClicked: backend.loadEncounterToNewRun(modelData.id)
                        }
                    }

                    // Reason / Clinical note
                    Text {
                        visible: (modelData.reason || "").length > 0
                        Layout.fillWidth: true
                        text: "Reason: " + modelData.reason
                        color: Theme.text
                        font.pixelSize: 12
                    }

                    // Lab test summary chips
                    RowLayout {
                        visible: (modelData.labSummary || "").length > 0
                        Layout.fillWidth: true
                        spacing: 6
                        Text {
                            text: "Labs:"
                            color: Theme.muted
                            font.pixelSize: 11
                            font.bold: true
                        }
                        Text {
                            text: modelData.labSummary
                            color: Theme.muted
                            font.pixelSize: 11
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }

                    // Symptoms tags
                    Flow {
                        visible: modelData.symptoms && modelData.symptoms.length > 0
                        Layout.fillWidth: true
                        spacing: 6
                        Repeater {
                            model: modelData.symptoms
                            delegate: Rectangle {
                                height: 20
                                radius: 10
                                implicitWidth: sympText.implicitWidth + 14
                                color: "#FEF3F2"
                                border.color: "#FDA29B"
                                Text {
                                    id: sympText
                                    anchors.centerIn: parent
                                    text: modelData
                                    color: "#B42318"
                                    font.pixelSize: 10
                                    font.bold: true
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
