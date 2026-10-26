import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"
import "pages"
import "."

ApplicationWindow {
    id: window
    width: 1440
    height: 900
    minimumWidth: 1120
    minimumHeight: 720
    visible: true
    visibility: Window.Maximized
    title: "HEMOGLYPH — Laboratory AI"
    color: Theme.background

    // ================================================================
    // ناوبری: نگاشت نام صفحه به ایندکس StackLayout
    // ================================================================
    function pageIndex(page) {
        var pages = {
            "home":        0,
            "newAnalysis": 1,
            "upload":      2,
            "manual":      3,
            "results":     4,
            "history":     5,
            "references":  6,
            "settings":    7,
            "guidelines":  8,
            "chat":        9,
            "riskmodels":  10
        }
        return pages[page] !== undefined ? pages[page] : 0
    }

    function pageTitle(page) {
        var titles = {
            "home":        "Home",
            "newAnalysis": "New analysis",
            "upload":      "Upload report",
            "manual":      "Manual input",
            "results":     "Results",
            "history":     "History",
            "references":  "References",
            "settings":    "Settings",
            "guidelines":  "Guidelines & clinical rules",
            "chat":        "AI assistant",
            "riskmodels":  "Risk models & scientific references"
        }
        return titles[page] || "Workspace"
    }

    // ================================================================
    // Software License Security Gate (Hardware-bound cryptographic lock)
    // ================================================================
    Loader {
        id: licenseLoader
        anchors.fill: parent
        active: backend ? (!backend.licenseValid && !backend.isRemotelyBlocked) : false
        sourceComponent: LicenseGate {}
        z: 20
    }

    // ================================================================
    // لایه ورود (نمایش فقط هنگام لاگین نبودن)
    // ================================================================
    Loader {
        id: loginLoader
        anchors.fill: parent
        active: backend ? (backend.licenseValid && !backend.loggedIn && !backend.isRemotelyBlocked) : false
        sourceComponent: LoginPage {}
        z: 10
    }

    // ================================================================
    // بدنه اصلی اپلیکیشن (نمایش فقط پس از ورود)
    // ================================================================
    RowLayout {
        id: mainLayout
        anchors.fill: parent
        spacing: 0
        visible: backend ? backend.loggedIn : false
        z: 1

        // ---- سایدبار ----
        Sidebar {
            Layout.fillHeight: true
        }

        // ---- محتوای اصلی ----
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // نوار بالایی
            TopBar {
                Layout.fillWidth: true
                title: window.pageTitle(backend ? backend.currentPage : "home")
            }

            // خط جداکننده
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.border
            }
            StackLayout {
                id: pageStack
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: window.pageIndex(backend ? backend.currentPage : "home")

                HomePage {}          // 0
                NewAnalysisPage {}   // 1
                UploadPage {}        // 2
                ManualPage {}        // 3
                ResultsPage {}       // 4
                HistoryPage {}       // 5
                ReferencesPage {}    // 6
                SettingsPage {}      // 7
                GuidelinesPage {}    // 8
                ChatPage {}          // 9
                RiskModelsPage {}    // 10
            }
        }
    }

    LoadingOverlay {
        z: 100
    }

    // ================================================================
    // First-Login / Onboarding OCR Activation Modal
    // ================================================================
    OcrActivationModal {
        id: ocrModal
        anchors.fill: parent
        z: 150
        visible: backend ? (backend.loggedIn && !backend.hasOcrApiKey && !dismissed) : false
    }

    Toast {
        id: toast
        anchors.top: parent.top
        anchors.right: parent.right       
        anchors.topMargin: 22
        anchors.rightMargin: 24
        z: 200
    }

    Connections {
        target: backend

        function onToast(level, message) {
            toast.show(level, message)
        }

        function onLoggedInChanged() {
            if (backend && backend.loggedIn) {
                ocrModal.reset()
            }
        }

        // ✅ ریست خودکار صفحات هنگام شروع آنالیز جدید
        function onAnalysisReset() {
            // StackLayout به‌صورت خودکار توسط backend.navigate مدیریت می‌شود
        }

        // ✅ تغییر تم
        function onCurrentPageChanged() {
            // عنوان نوار بالایی به‌صورت خودکار آپدیت می‌شود
        }
    }

    // ================================================================
    // تنظیمات اولیه
    // ================================================================
    Component.onCompleted: {
        console.log("Main.qml: Application window ready.")
        console.log("Main.qml: Pages count =", pageStack.count)
        console.log("Main.qml: Theme dark mode =", Theme.dark)
    }

    // ================================================================
    // پشتیبانی از کلیدهای میانبر
    // ================================================================
    Shortcut {
        sequence: "Ctrl+,"
        onActivated: backend.navigate("settings")
    }

    Shortcut {
        sequence: "Ctrl+H"
        onActivated: backend.navigate("home")
    }

    Shortcut {
        sequence: "Ctrl+N"
        onActivated: backend.newAnalysis()
    }

    Shortcut {
        sequence: "Escape"
        onActivated: {
            if (backend.currentPage !== "home") {
                backend.navigate("home")
            }
        }
    }

    // ================================================================
    // CRITICAL SECURITY: Central Command Remote Lockdown Shield
    // ================================================================
    Item {
        id: lockdownShield
        anchors.fill: parent
        z: 99999
        visible: backend ? backend.isRemotelyBlocked : false

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
                running: lockdownShield.visible
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

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 76; height: 76; radius: 38
                    color: "#20EF4444"
                    border.color: "#EF4444"
                    border.width: 2

                    Text {
                        anchors.centerIn: parent
                        text: "⛔"
                        font.pixelSize: 36
                    }

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
                            running: lockdownShield.visible
                            NumberAnimation { from: 1.0; to: 1.35; duration: 1200; easing.type: Easing.OutQuad }
                            NumberAnimation { from: 1.35; to: 1.0; duration: 1200; easing.type: Easing.InQuad }
                        }
                    }
                }

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
                            text: (backend && backend.remoteBlockReason && backend.remoteBlockReason.length > 0) ? backend.remoteBlockReason : "Workstation license suspended by administrator."
                            color: "#FFFFFF"
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                            wrapMode: Text.Wrap
                            lineHeight: 1.3
                        }
                    }
                }

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
                            text: backend ? backend.licenseMachineId : ""
                            color: "#F87171"
                            font.family: "Courier New, monospace"
                            font.pixelSize: 12
                            font.bold: true
                            horizontalAlignment: Text.AlignRight
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "All clinical diagnostic engines, local databases, and patient records have been locked to prevent unauthorized execution. Contact your software supervisor to restore authorization."
                    color: "#9CA3AF"
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    lineHeight: 1.3
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 8

                    Rectangle {
                        width: 8; height: 8; radius: 4
                        color: "#EF4444"

                        SequentialAnimation on opacity {
                            loops: Animation.Infinite
                            running: lockdownShield.visible
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
}
