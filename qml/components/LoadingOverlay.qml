import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property string blockReason: "Administrative suspension by central command."
    property string machineId: ""

    // Trap 100% of mouse, click, drag, and wheel events
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        preventStealing: true
        acceptedButtons: Qt.AllButtons
        cursorShape: Qt.ForbiddenCursor
        onClicked: (mouse) => mouse.accepted = true
        onPressed: (mouse) => mouse.accepted = true
        onReleased: (mouse) => mouse.accepted = true
        onDoubleClicked: (mouse) => mouse.accepted = true
        onWheel: (wheel) => wheel.accepted = true
    }

    // Deep Dark Void Background
    Rectangle {
        anchors.fill: parent
        color: "#070204"

        // Warning scanlines pattern
        Repeater {
            model: 24
            Rectangle {
                width: parent.width
                height: 1
                y: index * (parent.height / 24)
                color: "#15FF0033"
            }
        }
    }

    // Pulsing Red Emergency Border around entire window
    Rectangle {
        id: alarmBorder
        anchors.fill: parent
        color: "transparent"
        border.color: "#E11D48"
        border.width: 3

        SequentialAnimation on border.color {
            loops: Animation.Infinite
            running: root.visible
            ColorAnimation { from: "#E11D48"; to: "#7F1D1D"; duration: 800 }
            ColorAnimation { from: "#7F1D1D"; to: "#E11D48"; duration: 800 }
        }
    }

    // Main Emergency Card
    Rectangle {
        id: lockdownCard
        width: Math.min(parent.width - 48, 620)
        implicitHeight: cardLayout.implicitHeight + 64
        anchors.centerIn: parent
        radius: 18
        color: "#0F0508"
        border.color: "#DC2626"
        border.width: 1.5

        // Glowing backdrop blur simulation
        Rectangle {
            anchors.fill: parent
            anchors.margins: -4
            radius: 22
            z: -1
            color: "#25DC2626"
        }

        ColumnLayout {
            id: cardLayout
            anchors.fill: parent
            anchors.margins: 36
            spacing: 20

            // Top Hazard Emblem
            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                width: 76
                height: 76
                radius: 38
                color: "#20EF4444"
                border.color: "#EF4444"
                border.width: 2

                Text {
                    anchors.centerIn: parent
                    text: "⛔"
                    font.pixelSize: 36
                }

                // Pulsing outer radar ring
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width + 16
                    height: parent.height + 16
                    radius: width / 2
                    color: "transparent"
                    border.color: "#60EF4444"
                    border.width: 1

                    SequentialAnimation on scale {
                        loops: Animation.Infinite
                        running: root.visible
                        NumberAnimation { from: 1.0; to: 1.35; duration: 1200; easing.type: Easing.OutQuad }
                        NumberAnimation { from: 1.35; to: 1.0; duration: 1200; easing.type: Easing.InQuad }
                    }
                }
            }

            // Titles
            ColumnLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 6

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "SYSTEM ACCESS REVOKED"
                    color: "#F87171"
                    font.pixelSize: 22
                    font.weight: Font.Black
                    font.letterSpacing: 2
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "REMOTE KILL-SWITCH ACTIVATED BY CENTRAL COMMAND"
                    color: "#EF4444"
                    font.pixelSize: 11
                    font.weight: Font.Bold
                    font.letterSpacing: 1.2
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#30EF4444"
            }

            // Reason Box
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: reasonCol.implicitHeight + 24
                radius: 10
                color: "#18070B"
                border.color: "#50EF4444"
                border.width: 1

                ColumnLayout {
                    id: reasonCol
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8

                    Text {
                        text: "SUSPENSION NOTICE & REASON:"
                        color: "#FDA4AF"
                        font.pixelSize: 10
                        font.weight: Font.Bold
                        font.letterSpacing: 1
                    }

                    Text {
                        Layout.fillWidth: true
                        text: root.blockReason && root.blockReason.length > 0 ? root.blockReason : "Workstation license suspended by administrator."
                        color: "#FFFFFF"
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        wrapMode: Text.Wrap
                        lineHeight: 1.3
                    }
                }
            }

            // Workstation Machine ID Details
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 46
                radius: 8
                color: "#0A0305"
                border.color: "#30EF4444"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14

                    Text {
                        text: "TARGET MACHINE ID:"
                        color: "#9CA3AF"
                        font.pixelSize: 10
                        font.weight: Font.Bold
                    }

                    Text {
                        Layout.fillWidth: true
                        text: root.machineId
                        color: "#F87171"
                        font.family: "Courier New, monospace"
                        font.pixelSize: 12
                        font.bold: true
                        horizontalAlignment: Text.AlignRight
                    }
                }
            }

            // Explanatory note
            Text {
                Layout.fillWidth: true
                text: "All clinical diagnostic engines, local databases, and patient records have been locked to prevent unauthorized execution. If this is an administrative review or renewal, contact your software provider to restore access."
                color: "#9CA3AF"
                font.pixelSize: 11
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                lineHeight: 1.3
            }

            // Live status beacon
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 8

                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: "#EF4444"

                    SequentialAnimation on opacity {
                        loops: Animation.Infinite
                        running: root.visible
                        NumberAnimation { from: 1.0; to: 0.2; duration: 600 }
                        NumberAnimation { from: 0.2; to: 1.0; duration: 600 }
                    }
                }

                Text {
                    text: "LIVE SENTINEL LINK ACTIVE · WAITING FOR CENTRAL UNLOCK"
                    color: "#EF4444"
                    font.pixelSize: 10
                    font.weight: Font.Bold
                    font.letterSpacing: 0.8
                }
            }
        }
    }
}
