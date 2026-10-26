import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Rectangle {
    id: root
    property bool collapsed: backend ? backend.sidebarCollapsed : false
    width: collapsed ? 82 : 262
    color: Theme.sidebar
    Behavior on width { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

    readonly property bool aiOk: (backend && backend.chatConfigured !== undefined) ? backend.chatConfigured : true
    readonly property bool ocrOk: (!backend || backend.ocrError === undefined) ? true : (backend.ocrError.length === 0)
    readonly property bool engineOk: backend ? ((backend.ready === true) || (backend.featureCount > 0)) : false
    readonly property bool dbOk: backend ? ((backend.ready === true) || ((backend.appBuild || "").length > 0)) : false

    Flickable {
        id: sideFlick
        anchors.fill: parent
        anchors.margins: 14
        contentWidth: width
        contentHeight: sideCol.implicitHeight + 4
        clip: true
        interactive: contentHeight > height
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { width: 4 }

        ColumnLayout {
            id: sideCol
            width: parent.width
            spacing: 8

            /* ========== Logo ========== */
            MouseArea {
                Layout.fillWidth: true
                Layout.bottomMargin: 12
                height: 50
                cursorShape: Qt.PointingHandCursor
                onClicked: backend.navigate("home")
                RowLayout {
                    anchors.fill: parent
                    spacing: 10
                    Rectangle {
                        width: 42; height: 42; radius: 14
                        gradient: Gradient {
                            GradientStop { position: 0; color: Theme.accent }
                            GradientStop { position: 1; color: Theme.violet }
                        }
                        Text { anchors.centerIn: parent; text: "🧬"; font.pixelSize: 20 }
                    }
                    Text {
                        visible: !root.collapsed
                        text: "HEMOGLYPH"
                        color: "white"
                        font.family: Theme.fontFamily
                        font.weight: Font.Bold
                        font.letterSpacing: 2
                        Layout.fillWidth: true
                    }
                    ToolButton {
                        id: collapseButton
                        visible: !root.collapsed
                        text: "‹"
                        onClicked: backend.toggleSidebar()
                        contentItem: Text { text: collapseButton.text; color: "#9BADBF"; font.pixelSize: 25; horizontalAlignment: Text.AlignHCenter }
                        background: Rectangle { color: collapseButton.hovered ? "#1B263B" : "transparent"; radius: 9 }
                    }
                }
            }

            ToolButton {
                id: expandButton
                visible: root.collapsed
                Layout.alignment: Qt.AlignHCenter
                text: "☰"
                onClicked: backend.toggleSidebar()
                contentItem: Text { text: expandButton.text; color: "#B9C6D8"; font.pixelSize: 18; horizontalAlignment: Text.AlignHCenter }
                background: Rectangle { color: expandButton.hovered ? "#1B263B" : "transparent"; radius: 10 }
            }

            /* ========== Navigation ========== */
            NavButton { iconText: "🏠"; label: "Home"; target: "home"; collapsed: root.collapsed }
            NavButton { iconText: "+"; label: "New analysis"; target: "newAnalysis"; collapsed: root.collapsed }
            NavButton {
                iconText: "💬"
                label: "AI assistant"
                target: "chat"
                collapsed: root.collapsed
                extraAction: function() { backend.loadChatHistory() }
            }
            NavButton { iconText: "◷"; label: "History"; target: "history"; collapsed: root.collapsed }
            NavButton { iconText: "▣"; label: "References"; target: "references"; collapsed: root.collapsed }
            NavButton { iconText: "◈"; label: "Guidelines"; target: "guidelines"; collapsed: root.collapsed }
            
            // ✅ دکمه جدید Risk Models
            NavButton { 
                iconText: "📐"; 
                label: "Risk models"; 
                target: "riskmodels"; 
                collapsed: root.collapsed 
            }

            /* ========== Chat history (auto-saved) - Hidden in release build ========== */
            RowLayout {
                visible: false
                Layout.fillWidth: true
                Layout.leftMargin: 14
                Layout.topMargin: 12
                Layout.bottomMargin: 2
                spacing: 6
                Text { text: "CHAT HISTORY"; color: "#7E93B4"; font.pixelSize: 9; font.bold: true; font.letterSpacing: 1.4 }
                Text { text: "(" + (backend && backend.chatHistoryRows ? backend.chatHistoryRows.length : 0) + ")"; color: "#5A6E8C"; font.pixelSize: 9 }
                Item { Layout.fillWidth: true }
            }
            Rectangle {
                visible: false
                Layout.fillWidth: true
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                implicitHeight: 44
                radius: 9
                color: "#0F1A2E"
                Text { anchors.centerIn: parent; text: "No saved chats yet"; color: "#7E93B4"; font.pixelSize: 10 }
            }
            ListView {
                id: chatHistoryList
                visible: false
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(contentHeight, 216)
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                model: backend ? backend.chatHistoryRows : []
                clip: true
                spacing: 3
                ScrollBar.vertical: ScrollBar { width: 4 }
                delegate: Rectangle {
                    id: chatItem
                    required property int sessionId
                    required property int analysisId
                    required property string title
                    required property string date
                    required property string summary
                    width: ListView.view ? ListView.view.width : 0
                    height: 44
                    radius: 9
                    color: (backend && backend.currentChatSessionId === chatItem.sessionId) ? "#1A3655"
                         : itemMouse.containsMouse ? "#17253A" : "transparent"
                    border.color: (backend && backend.currentChatSessionId === chatItem.sessionId) ? "#27557D" : "transparent"
                    MouseArea {
                        id: itemMouse
                        anchors.fill: parent
                        anchors.rightMargin: 26
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: backend.openChatSession(chatItem.sessionId)
                    }
                    ToolButton {
                        id: deleteChatBtn
                        anchors.right: parent.right
                        anchors.rightMargin: 3
                        anchors.verticalCenter: parent.verticalCenter
                        width: 22; height: 22
                        text: "×"
                        ToolTip.visible: hovered
                        ToolTip.text: "Delete chat"
                        contentItem: Text {
                            text: deleteChatBtn.text
                            color: "#FDA29B"
                            font.pixelSize: 14
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle { color: deleteChatBtn.hovered ? "#3D1F1F" : "transparent"; radius: 6 }
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            acceptedButtons: Qt.NoButton
                        }
                        onClicked: backend.deleteChatSession(chatItem.sessionId)
                    }
                    Column {
                        anchors.left: parent.left
                        anchors.leftMargin: 12
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: deleteChatBtn.left
                        anchors.rightMargin: 6
                        spacing: 2
                        Text {
                            width: parent.width
                            text: "💬 " + chatItem.title
                            color: "#DDE6F2"
                            font.pixelSize: 11
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        Text {
                            width: parent.width
                            text: chatItem.date
                            color: "#7E93B4"
                            font.pixelSize: 9
                            elide: Text.ElideRight
                        }
                    }
                }
            }
            ToolButton {
                visible: false // Hidden in release build while chat is under development
                Layout.fillWidth: true
                Layout.topMargin: 2
                implicitHeight: 36
                text: "+ New chat"
                contentItem: Text {
                    text: parent.text
                    color: "#B9C7D9"
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignHCenter
                }
                background: Rectangle {
                    color: parent.hovered ? "#17253A" : "transparent"
                    radius: 9
                    border.color: "#21304A"
                }
                onClicked: backend.newChatSession()
            }
            Item { Layout.preferredHeight: 8 }

            /* ========== System status ========== */
            Rectangle {
                visible: !root.collapsed
                Layout.fillWidth: true
                implicitHeight: statusCol.implicitHeight + 20
                radius: 12
                color: "#0F1A2E"
                ColumnLayout {
                    id: statusCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 10
                    spacing: 6
                    Text { text: "SYSTEM STATUS"; color: "#7E93B4"; font.pixelSize: 9; font.bold: true; font.letterSpacing: 1.4 }
                    StatusDot {
                        label: "AI assistant"
                        isDev: true
                    }
                    StatusDot { label: "OCR engine"; ok: root.ocrOk }
                    StatusDot { label: "Analysis engine"; ok: root.engineOk }
                    StatusDot { label: "Database"; ok: root.dbOk }
                }
            }

            /* ========== Bottom buttons ========== */
            NavButton { iconText: Theme.dark ? "☀" : "◐"; label: Theme.dark ? "Light mode" : "Dark mode"; target: "theme"; collapsed: root.collapsed }
            NavButton { iconText: "⚙"; label: "Settings"; target: "settings"; collapsed: root.collapsed }
            Rectangle { Layout.fillWidth: true; height: 1; color: "#21304A"; Layout.topMargin: 6; Layout.bottomMargin: 6 }

            /* ========== User row ========== */
            RowLayout {
                Layout.fillWidth: true
                Rectangle {
                    width: 36; height: 36; radius: 12; color: "#20304A"
                    Text { anchors.centerIn: parent; text: (backend && backend.userName && backend.userName.length) ? backend.userName[0].toUpperCase() : "U"; color: "white"; font.bold: true }
                }
                ColumnLayout {
                    visible: !root.collapsed; spacing: 0; Layout.fillWidth: true
                    Text { text: backend ? backend.userName : ""; color: "white"; font.pixelSize: 13; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                    Text { text: backend ? backend.userEmail : ""; color: "#8192AA"; font.pixelSize: 10; elide: Text.ElideRight; Layout.fillWidth: true }
                }
                ToolButton {
                    id: logoutButton
                    visible: !root.collapsed; text: "↪"
                    onClicked: if (backend) backend.logout()
                    contentItem: Text { text: logoutButton.text; color: "#91A1B8"; horizontalAlignment: Text.AlignHCenter }
                    background: Rectangle { color: logoutButton.hovered ? "#1B263B" : "transparent"; radius: 8 }
                }
            }
        }
    }

    /* ========== Status dot component ========== */
    component StatusDot: RowLayout {
        property string label: ""
        property bool ok: true
        property bool isDev: false
        property string customStatusText: ""
        spacing: 6
        Rectangle {
            width: 8; height: 8; radius: 4
            color: isDev ? "#38BDF8" : (ok ? "#12B76A" : "#F04438")
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                running: !ok && !isDev
                NumberAnimation { from: 1; to: 0.35; duration: 700 }
                NumberAnimation { from: 0.35; to: 1; duration: 700 }
            }
        }
        Text {
            text: label
            color: isDev ? "#BAE6FD" : (ok ? "#75E0A7" : "#FDA29B")
            font.pixelSize: 10
            font.weight: isDev ? Font.Medium : Font.Normal
            Layout.fillWidth: true
            elide: Text.ElideRight
        }
        Text {
            text: customStatusText.length > 0 ? customStatusText : (isDev ? "DEV" : (ok ? "OK" : "OFF"))
            color: isDev ? "#38BDF8" : (ok ? "#75E0A7" : "#FDA29B")
            font.pixelSize: 8
            font.bold: true
        }
    }

    /* ========== Nav button component ========== */
    component NavButton: Button {
        id: navControl
        required property string iconText
        required property string label
        required property string target
        required property bool collapsed
        property var extraAction: null
        Layout.fillWidth: true
        implicitHeight: 44
        onClicked: {
            if (target === "theme") Theme.dark = !Theme.dark
            else if (target.length > 0) backend.navigate(target)
            if (extraAction) extraAction()
        }
        contentItem: RowLayout {
            spacing: 13
            Text { text: navControl.iconText; color: "#B9C7D9"; font.pixelSize: 17; Layout.preferredWidth: 24; horizontalAlignment: Text.AlignHCenter }
            Text { visible: !navControl.collapsed; text: navControl.label; color: "#DDE6F2"; font.family: Theme.fontFamily; font.pixelSize: 13; font.weight: Font.Medium; Layout.fillWidth: true }
        }
        background: Rectangle {
            radius: 11
            color: navControl.target !== "theme" && navControl.target.length > 0 && backend && backend.currentPage === navControl.target ? "#1A3655" : navControl.hovered ? "#17253A" : "transparent"
            border.color: navControl.target !== "theme" && navControl.target.length > 0 && backend && backend.currentPage === navControl.target ? "#27557D" : "transparent"
        }
        ToolTip.visible: collapsed && hovered
        ToolTip.text: label
    }
}