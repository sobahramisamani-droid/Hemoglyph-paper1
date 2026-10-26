import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import ".."

Item {
    id: root

    Rectangle {
        anchors.fill: parent
        color: Theme.background
    }

    // Ambient background particle grid
    Repeater {
        model: 16
        Rectangle {
            width: 80 + (index % 4) * 20; height: width; radius: width / 2
            x: (index * 163) % Math.max(root.width, 1) - 30
            y: (index * 113) % Math.max(root.height, 1) - 30
            color: index % 2 ? "#0823BFE5" : "#067558F5"
            border.color: index % 2 ? "#1023BFE5" : "#0C7558F5"
        }
    }

    HgCard {
        id: gateCard
        width: Math.min(parent.width - 40, 560)
        implicitHeight: cardCol.implicitHeight + 64
        anchors.centerIn: parent

        ColumnLayout {
            id: cardCol
            anchors.fill: parent
            anchors.margins: 32
            spacing: 16

            // Header Icon
            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                width: 64; height: 64; radius: 20
                gradient: Gradient {
                    GradientStop { position: 0; color: Theme.accent }
                    GradientStop { position: 1; color: Theme.violet }
                }
                Text { anchors.centerIn: parent; text: "🛡️"; font.pixelSize: 30 }
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "HEMOGLYPH SECURITY GATE"
                color: Theme.text
                font.pixelSize: 20
                font.weight: Font.Bold
                font.letterSpacing: 2
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.fillWidth: true
                text: "This software is cryptographically protected and bound to hardware. To activate your installation, provide your Machine ID to your administrator."
                color: Theme.muted
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                lineHeight: 1.3
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.border
            }

            // Machine ID Section
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                Text {
                    text: "YOUR HARDWARE MACHINE ID"
                    color: Theme.muted
                    font.pixelSize: 10
                    font.weight: Font.Bold
                    font.letterSpacing: 1
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 44
                        radius: 10
                        color: Theme.surfaceAlt
                        border.color: Theme.border
                        border.width: 1

                        TextEdit {
                            id: midDisplay
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            verticalAlignment: TextEdit.AlignVCenter
                            readOnly: true
                            selectByMouse: true
                            text: backend ? backend.licenseMachineId : "HG-PROBING-HARDWARE"
                            color: Theme.accent
                            font.family: "Courier New, monospace"
                            font.pixelSize: 14
                            font.bold: true
                        }
                    }

                    HgButton {
                        text: "📋 Copy ID"
                        implicitHeight: 44
                        onClicked: {
                            if (backend) {
                                backend.copyMachineId()
                                backend.toast("success", "Machine ID copied to clipboard!")
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 6
                    Text {
                        text: "Request key via email:"
                        color: Theme.muted
                        font.pixelSize: 11
                    }
                    Text {
                        text: "sobahramisamani@gmail.com"
                        color: Theme.accent
                        font.pixelSize: 11
                        font.bold: true
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Qt.openUrlExternally("mailto:sobahramisamani@gmail.com?subject=HEMOGLYPH%20Activation%20Key%20Request&body=Hello,%20please%20activate%20my%20HEMOGLYPH%20installation.%20My%20Machine%20ID%20is:%20" + (backend ? backend.licenseMachineId : ""))
                        }
                    }
                }
            }

            // Activation Key Input Section
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                Text {
                    text: "ACTIVATION LICENSE KEY"
                    color: Theme.muted
                    font.pixelSize: 10
                    font.weight: Font.Bold
                    font.letterSpacing: 1
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 74
                    radius: 10
                    color: Theme.surfaceAlt
                    border.color: keyInput.activeFocus ? Theme.accent : Theme.border
                    border.width: keyInput.activeFocus ? 1.5 : 1

                    ScrollView {
                        anchors.fill: parent
                        anchors.margins: 8

                        TextArea {
                            id: keyInput
                            placeholderText: "Paste your HGLIC-... cryptographic license key here"
                            placeholderTextColor: Theme.muted
                            color: Theme.text
                            font.pixelSize: 11
                            font.family: "Courier New, monospace"
                            wrapMode: TextEdit.Wrap
                            background: null
                        }
                    }
                }
            }

            // Error display banner if any
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: errText.implicitHeight + 16
                radius: 8
                color: "#FEF3F2"
                border.color: "#FDA29B"
                border.width: 1
                visible: (backend && backend.licenseError && backend.licenseError.length > 0) || false

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 8
                    Text { text: "⚠"; color: "#B42318"; font.pixelSize: 12 }
                    Text {
                        id: errText
                        Layout.fillWidth: true
                        text: backend ? backend.licenseError : ""
                        color: "#B42318"
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                    }
                }
            }

            // Action Button
            HgButton {
                Layout.fillWidth: true
                implicitHeight: 46
                text: "Activate HEMOGLYPH"
                primary: true
                onClicked: {
                    var k = keyInput.text.trim()
                    if (!k.length) {
                        backend.toast("warning", "Please paste an activation license key.")
                        return
                    }
                    var success = backend.activateLicense(k)
                    if (success) {
                        backend.toast("success", "License verified and activated successfully!")
                    } else {
                        backend.toast("error", "License activation failed. Verify your key and Machine ID.")
                    }
                }
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "Zero cloud communication · Cryptographic offline verification"
                color: Theme.muted
                font.pixelSize: 10
            }
        }
    }
}
