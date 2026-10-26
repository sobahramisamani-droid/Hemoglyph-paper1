import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import ".."

Item {
    id: root

    property bool dismissed: false

    function dismiss() {
        dismissed = true
    }

    function reset() {
        dismissed = false
        keyInput.text = ""
        keyInput.errorMsg = ""
    }

    // Scrim: Dims the main screen behind the modal
    Rectangle {
        id: scrim
        anchors.fill: parent
        color: "#000000"
        opacity: 0.65

        Behavior on opacity {
            NumberAnimation { duration: 200 }
        }

        MouseArea {
            anchors.fill: parent
            // Swallow all clicks behind modal; clicking outside closes
            onClicked: root.dismiss()
        }
    }

    HgCard {
        id: modalCard
        width: Math.min(parent.width - 40, 580)
        implicitHeight: modalCol.implicitHeight + 48
        anchors.centerIn: parent

        // Trap clicks inside card so they don't dismiss the modal
        MouseArea {
            anchors.fill: parent
        }

        ColumnLayout {
            id: modalCol
            anchors.fill: parent
            anchors.margins: 28
            spacing: 16

            // Header Row
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Rectangle {
                    width: 48
                    height: 48
                    radius: 14
                    gradient: Gradient {
                        GradientStop { position: 0; color: Theme.accent }
                        GradientStop { position: 1; color: Theme.violet }
                    }
                    Text {
                        anchors.centerIn: parent
                        text: "📷"
                        font.pixelSize: 24
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: "Activate Lab Report Scanner (Vision OCR)"
                        color: Theme.text
                        font.family: Theme.fontFamily
                        font.pixelSize: 16
                        font.weight: Font.Bold
                    }

                    Text {
                        text: "فعال‌سازی هوش مصنوعی استخراج تصاویر آزمایش"
                        color: Theme.muted
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                    }
                }

                // Close Button (✕)
                Rectangle {
                    width: 32
                    height: 32
                    radius: 16
                    color: closeArea.containsMouse ? (Theme.dark ? "#334155" : "#E2E8F0") : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: "✕"
                        color: Theme.muted
                        font.pixelSize: 14
                        font.weight: Font.Bold
                    }

                    MouseArea {
                        id: closeArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.dismiss()
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.border
            }

            // Description & Instruction
            Text {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                lineHeight: 1.4
                font.family: Theme.fontFamily
                font.pixelSize: 12
                color: Theme.text
                text: "To automatically scan paper lab reports, photos, and scanned PDFs, activate the high-speed Groq Vision OCR engine. You can obtain a free API key in seconds."
            }

            // Step 1: Open Groq Console Button
            HgButton {
                Layout.fillWidth: true
                implicitHeight: 40
                text: "🌐 Open Groq Console (console.groq.com) — دریافت کلید رایگان"
                onClicked: Qt.openUrlExternally("https://console.groq.com/keys")
            }

            // High-Visibility VPN Warning Box
            Rectangle {
                Layout.fillWidth: true
                radius: 10
                color: Theme.dark ? "#422006" : "#FEFCE8"
                border.color: Theme.dark ? "#854D0E" : "#FEF08A"
                border.width: 1
                implicitHeight: vpnCol.implicitHeight + 20

                RowLayout {
                    id: vpnCol
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 10

                    Text {
                        text: "⚠️"
                        font.pixelSize: 22
                        Layout.alignment: Qt.AlignTop
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text: "Important: VPN Required (اتصال به فیلترشکن / VPN الزامی است)"
                            color: Theme.dark ? "#FDE047" : "#854D0E"
                            font.family: Theme.fontFamily
                            font.pixelSize: 12
                            font.weight: Font.Bold
                        }

                        Text {
                            Layout.fillWidth: true
                            text: "Due to provider geographic restrictions, an active VPN is required both to open console.groq.com and when scanning lab images inside the software."
                            color: Theme.dark ? "#FEF08A" : "#713F12"
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            wrapMode: Text.Wrap
                            lineHeight: 1.3
                        }

                        Text {
                            Layout.fillWidth: true
                            text: "به دلیل تحریم‌های شرکت ارائه‌دهنده، هم جهت ثبت‌نام و دریافت کلید در سایت Groq و هم هنگام اسکن تصویر در نرم‌افزار، فعال بودن فیلترشکن ضروری است."
                            color: Theme.dark ? "#FEF08A" : "#713F12"
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            wrapMode: Text.Wrap
                            lineHeight: 1.3
                        }
                    }
                }
            }

            // Input Field Section
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                Text {
                    text: "GROQ API KEY (کلید دسترسی)"
                    color: Theme.muted
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    font.weight: Font.Bold
                    font.letterSpacing: 0.5
                }

                HgField {
                    id: keyInput
                    Layout.fillWidth: true
                    placeholderText: "Paste your Groq API key here (starts with gsk_...)"
                    echoMode: showKeyToggle.checked ? TextInput.Normal : TextInput.Password
                    property string errorMsg: ""
                }

                RowLayout {
                    Layout.fillWidth: true
                    CheckBox {
                        id: showKeyToggle
                        text: "Show Key"
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: keyInput.errorMsg
                        color: Theme.danger
                        font.pixelSize: 11
                        visible: keyInput.errorMsg.length > 0
                    }
                }
            }

            // Buttons Action Row
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                HgButton {
                    text: "Skip for Now (رد کردن)"
                    Layout.fillWidth: true
                    implicitHeight: 44
                    onClicked: root.dismiss()
                }

                HgButton {
                    text: "Save & Activate OCR (ذخیره و فعال‌سازی)"
                    primary: true
                    Layout.fillWidth: true
                    implicitHeight: 44
                    onClicked: {
                        var k = keyInput.text.trim()
                        if (k.length < 10 || !k.startsWith("gsk_")) {
                            keyInput.errorMsg = "Key should start with 'gsk_' (حداقل ۱۰ کاراکتر)"
                            return
                        }
                        if (backend) {
                            backend.setOcrApiKey(k)
                            backend.toast("success", "Groq Vision OCR activated successfully!")
                        }
                        root.dismiss()
                    }
                }
            }
        }
    }
}
