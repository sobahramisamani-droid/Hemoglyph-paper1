import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import ".."

Item {
    id: root
    property bool registerMode: false
    property bool showPassword: false
    property var passwordInfo: ({"score": 0, "strong": false, "missing": []})

    // Ambient Medical Background
    Rectangle {
        anchors.fill: parent
        color: Theme.background

        Repeater {
            model: 14
            Rectangle {
                width: 90 + (index % 4) * 22
                height: width
                radius: width / 2
                x: (index * 173) % Math.max(root.width, 1) - 40
                y: (index * 109) % Math.max(root.height, 1) - 20
                color: index % 2 ? "#0A23BFE5" : "#087558F5"
                border.color: index % 2 ? "#1323BFE5" : "#107558F5"
            }
        }
    }

    // Scroll container so form is 100% accessible on any laptop or small window
    Flickable {
        id: scroller
        anchors.fill: parent
        contentWidth: width
        contentHeight: Math.max(height, loginCard.height + 40)
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        HgCard {
            id: loginCard
            width: Math.min(scroller.width - 32, root.registerMode ? 460 : 420)
            height: root.registerMode ? 700 : ((backend && backend.hasRememberedEmail) ? 585 : 510)
            anchors.horizontalCenter: parent.horizontalCenter
            y: Math.max(20, (scroller.height - height) / 2)
            radius: Theme.radius

            Behavior on height {
                NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 10

                // 1. BRAND HEADER
                ColumnLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 4

                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        width: 52
                        height: 52
                        radius: 16
                        gradient: Gradient {
                            GradientStop { position: 0; color: Theme.accent }
                            GradientStop { position: 1; color: Theme.violet }
                        }
                        Text {
                            anchors.centerIn: parent
                            text: "🧬"
                            font.pixelSize: 24
                        }
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "HEMOGLYPH ALA3"
                        color: Theme.text
                        font.family: Theme.fontFamily
                        font.pixelSize: 19
                        font.bold: true
                        font.letterSpacing: 2
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "CLINICAL DECISION SUPPORT PLATFORM"
                        color: Theme.accent
                        font.family: Theme.fontFamily
                        font.pixelSize: 9
                        font.weight: Font.DemiBold
                        font.letterSpacing: 1.5
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.topMargin: 2
                        text: root.registerMode ? "Create your laboratory workspace" : "Authorized Clinician Sign-In"
                        color: Theme.muted
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                    }
                }

                // 2. SAVED ACCOUNT TILE (Sign-in mode only)
                Rectangle {
                    id: rememberedAccount
                    visible: !root.registerMode && (backend && backend.hasRememberedEmail)
                    Layout.fillWidth: true
                    implicitHeight: visible ? 58 : 0
                    radius: 12
                    color: Theme.surfaceAlt
                    border.color: Theme.border

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 10

                        Rectangle {
                            width: 38
                            height: 38
                            radius: 11
                            color: "#1823BFE5"
                            Text {
                                anchors.centerIn: parent
                                text: (backend && backend.rememberedEmail && backend.rememberedEmail.length > 0)
                                      ? backend.rememberedEmail[0].toUpperCase() : "U"
                                color: Theme.accent
                                font.family: Theme.fontFamily
                                font.pixelSize: 15
                                font.bold: true
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1

                            Text {
                                text: "Continue with saved account"
                                color: Theme.text
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                            }
                            Text {
                                text: (backend && backend.rememberedEmail) ? backend.rememberedEmail : ""
                                color: Theme.muted
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }

                        Text {
                            text: "→"
                            color: Theme.accent
                            font.pixelSize: 18
                            font.bold: true
                        }

                        ToolButton {
                            id: forgetButton
                            implicitWidth: 28
                            implicitHeight: 28
                            text: "×"
                            onClicked: if (backend) backend.forgetRememberedEmail()
                            contentItem: Text {
                                text: forgetButton.text
                                color: Theme.muted
                                font.pixelSize: 16
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle {
                                color: forgetButton.hovered ? Qt.rgba(0,0,0,0.06) : "transparent"
                                radius: 8
                            }
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                acceptedButtons: Qt.NoButton
                            }
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        anchors.rightMargin: 36
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (backend && backend.rememberedEmail) {
                                emailField.text = backend.rememberedEmail
                                passwordField.forceActiveFocus()
                            }
                        }
                    }
                }

                // 3. FORM FIELDS WITH CLEAR LABELS & HIGH CONTRAST

                // FULL NAME (Register only)
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3
                    visible: root.registerMode

                    Text {
                        text: "FULL NAME"
                        color: Theme.text
                        font.family: Theme.fontFamily
                        font.pixelSize: 10
                        font.bold: true
                        opacity: 0.8
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 42
                        radius: 10
                        color: Theme.surfaceAlt
                        border.color: nameField.activeFocus ? Theme.accent : Theme.border
                        border.width: nameField.activeFocus ? 1.5 : 1

                        TextField {
                            id: nameField
                            anchors.fill: parent
                            leftPadding: 12
                            rightPadding: 12
                            placeholderText: "e.g. Sobhan Bahrami"
                            color: Theme.text
                            placeholderTextColor: Theme.muted
                            horizontalAlignment: TextInput.AlignLeft
                            verticalAlignment: TextInput.AlignVCenter
                            background: null
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                        }
                    }
                }

                // EMAIL FIELD
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3

                    Text {
                        text: "WORKSPACE EMAIL"
                        color: Theme.text
                        font.family: Theme.fontFamily
                        font.pixelSize: 10
                        font.bold: true
                        opacity: 0.8
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 42
                        radius: 10
                        color: Theme.surfaceAlt
                        border.color: emailField.activeFocus ? Theme.accent : Theme.border
                        border.width: emailField.activeFocus ? 1.5 : 1

                        TextField {
                            id: emailField
                            anchors.fill: parent
                            leftPadding: 12
                            rightPadding: 12
                            placeholderText: "clinician@hospital.org"
                            inputMethodHints: Qt.ImhEmailCharactersOnly
                            color: Theme.text
                            placeholderTextColor: Theme.muted
                            horizontalAlignment: TextInput.AlignLeft
                            verticalAlignment: TextInput.AlignVCenter
                            background: null
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                            onAccepted: passwordField.forceActiveFocus()
                        }
                    }
                }

                // PASSWORD FIELD
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3

                    Text {
                        text: "PASSWORD"
                        color: Theme.text
                        font.family: Theme.fontFamily
                        font.pixelSize: 10
                        font.bold: true
                        opacity: 0.8
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 42
                        radius: 10
                        color: Theme.surfaceAlt
                        border.color: passwordField.activeFocus ? Theme.accent : Theme.border
                        border.width: passwordField.activeFocus ? 1.5 : 1

                        TextField {
                            id: passwordField
                            anchors.left: parent.left
                            anchors.right: eyeButton.left
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            leftPadding: 12
                            rightPadding: 12
                            placeholderText: root.registerMode ? "Min 8 chars, 1 uppercase, 1 digit, 1 symbol" : "Enter password"
                            echoMode: root.showPassword ? TextInput.Normal : TextInput.Password
                            color: Theme.text
                            placeholderTextColor: Theme.muted
                            horizontalAlignment: TextInput.AlignLeft
                            verticalAlignment: TextInput.AlignVCenter
                            background: null
                            font.family: Theme.fontFamily
                            font.pixelSize: 13

                            onTextChanged: {
                                if (root.registerMode && backend) {
                                    root.passwordInfo = backend.assessPassword(text)
                                }
                            }
                            onAccepted: {
                                if (root.registerMode) {
                                    confirmField.forceActiveFocus()
                                } else if (emailField.text.length && text.length && backend) {
                                    backend.login(emailField.text, text)
                                }
                            }
                        }

                        ToolButton {
                            id: eyeButton
                            anchors.right: parent.right
                            anchors.rightMargin: 4
                            anchors.verticalCenter: parent.verticalCenter
                            width: 34
                            height: 34
                            text: root.showPassword ? "👁" : "🔒"
                            ToolTip.visible: hovered
                            ToolTip.text: root.showPassword ? "Hide password" : "Show password"
                            onClicked: root.showPassword = !root.showPassword
                            contentItem: Text {
                                text: eyeButton.text
                                color: Theme.muted
                                font.pixelSize: 14
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle {
                                radius: 8
                                color: eyeButton.hovered ? Qt.rgba(0,0,0,0.06) : "transparent"
                            }
                        }
                    }
                }

                // CONFIRM PASSWORD (Register only)
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3
                    visible: root.registerMode

                    Text {
                        text: "CONFIRM PASSWORD"
                        color: Theme.text
                        font.family: Theme.fontFamily
                        font.pixelSize: 10
                        font.bold: true
                        opacity: 0.8
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 42
                        radius: 10
                        color: Theme.surfaceAlt
                        border.color: confirmField.activeFocus ? Theme.accent : Theme.border
                        border.width: confirmField.activeFocus ? 1.5 : 1

                        TextField {
                            id: confirmField
                            anchors.left: parent.left
                            anchors.right: confirmEye.left
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            leftPadding: 12
                            rightPadding: 12
                            placeholderText: "Re-enter your password"
                            echoMode: root.showPassword ? TextInput.Normal : TextInput.Password
                            color: Theme.text
                            placeholderTextColor: Theme.muted
                            horizontalAlignment: TextInput.AlignLeft
                            verticalAlignment: TextInput.AlignVCenter
                            background: null
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                        }

                        ToolButton {
                            id: confirmEye
                            anchors.right: parent.right
                            anchors.rightMargin: 4
                            anchors.verticalCenter: parent.verticalCenter
                            width: 34
                            height: 34
                            text: root.showPassword ? "👁" : "🔒"
                            onClicked: root.showPassword = !root.showPassword
                            contentItem: Text {
                                text: confirmEye.text
                                color: Theme.muted
                                font.pixelSize: 14
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle {
                                radius: 8
                                color: confirmEye.hovered ? Qt.rgba(0,0,0,0.06) : "transparent"
                            }
                        }
                    }
                }

                // PASSWORD STRENGTH METER (Register only)
                ColumnLayout {
                    visible: root.registerMode
                    Layout.fillWidth: true
                    spacing: 4

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Repeater {
                            model: 4
                            Rectangle {
                                Layout.fillWidth: true
                                height: 4
                                radius: 2
                                color: {
                                    var score = (root.passwordInfo && root.passwordInfo.score) ? root.passwordInfo.score : 0
                                    if (index < score) {
                                        if (root.passwordInfo && root.passwordInfo.strong) return Theme.success
                                        if (score >= 2) return Theme.warning
                                        return Theme.danger
                                    }
                                    return Theme.border
                                }
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true

                        Text {
                            Layout.fillWidth: true
                            text: {
                                if (!passwordField.text.length) return "Password requirement: 8+ chars, uppercase, number, symbol"
                                if (root.passwordInfo && root.passwordInfo.strong) return "✓ Password strength: Excellent"
                                var miss = (root.passwordInfo && root.passwordInfo.missing) ? root.passwordInfo.missing.join(", ") : ""
                                return "Add: " + miss
                            }
                            color: {
                                if (!passwordField.text.length) return Theme.muted
                                if (root.passwordInfo && root.passwordInfo.strong) return Theme.success
                                return Theme.warning
                            }
                            font.family: Theme.fontFamily
                            font.pixelSize: 10
                            elide: Text.ElideRight
                        }

                        Text {
                            visible: confirmField.text.length > 0
                            text: confirmField.text === passwordField.text ? "✓ Match" : "✕ No match"
                            color: confirmField.text === passwordField.text ? Theme.success : Theme.danger
                            font.family: Theme.fontFamily
                            font.pixelSize: 10
                            font.bold: true
                        }
                    }
                }

                // BIRTH DATE (Register only)
                ColumnLayout {
                    visible: root.registerMode
                    Layout.fillWidth: true
                    spacing: 3

                    Text {
                        text: "BIRTH DATE"
                        color: Theme.text
                        font.family: Theme.fontFamily
                        font.pixelSize: 10
                        font.bold: true
                        opacity: 0.8
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 42
                        radius: 10
                        color: Theme.surfaceAlt
                        border.color: birthField.activeFocus ? Theme.accent : Theme.border
                        border.width: birthField.activeFocus ? 1.5 : 1

                        TextField {
                            id: birthField
                            anchors.fill: parent
                            leftPadding: 12
                            rightPadding: 12
                            text: "1990-01-01"
                            placeholderText: "YYYY-MM-DD"
                            color: Theme.text
                            placeholderTextColor: Theme.muted
                            horizontalAlignment: TextInput.AlignLeft
                            verticalAlignment: TextInput.AlignVCenter
                            background: null
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                        }
                    }
                }

                // 4. ACTION BUTTON
                HgButton {
                    id: mainButton
                    Layout.fillWidth: true
                    implicitHeight: 44
                    primary: true
                    enabled: {
                        if (root.registerMode) {
                            return emailField.text.length > 3 &&
                                   passwordField.text.length >= 8 &&
                                   nameField.text.length > 1 &&
                                   confirmField.text === passwordField.text &&
                                   (root.passwordInfo && root.passwordInfo.strong)
                        } else {
                            return emailField.text.length > 3 && passwordField.text.length > 0
                        }
                    }
                    text: root.registerMode ? "Create account" : "Sign in"

                    onClicked: {
                        if (root.registerMode) {
                            if (backend) {
                                backend.register(
                                    nameField.text,
                                    emailField.text,
                                    passwordField.text,
                                    confirmField.text,
                                    birthField.text,
                                    "Female"
                                )
                            }
                        } else {
                            if (backend) {
                                backend.login(emailField.text, passwordField.text)
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: Theme.border
                    Layout.topMargin: 2
                    Layout.bottomMargin: 2
                }

                // 5. TOGGLE MODE BUTTON
                HgButton {
                    Layout.fillWidth: true
                    implicitHeight: 38
                    text: root.registerMode ? "← Back to sign in" : "Create an account"
                    onClicked: {
                        root.registerMode = !root.registerMode
                        passwordField.text = ""
                        confirmField.text = ""
                        root.showPassword = false
                        if (!root.registerMode && backend && backend.hasRememberedEmail) {
                            emailField.text = backend.rememberedEmail
                        } else {
                            emailField.text = ""
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                // 6. FOOTER NOTES
                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    text: "Passwords are never stored in settings. Only the last successful email can be remembered."
                    color: Theme.muted
                    font.family: Theme.fontFamily
                    font.pixelSize: 9
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: (backend && backend.appBuild) ? backend.appBuild : "HEMOGLYPH ALA3"
                    color: Theme.border
                    font.family: Theme.fontFamily
                    font.pixelSize: 8
                }
            }
        }
    }

    Component.onCompleted: {
        if (backend && backend.hasRememberedEmail) {
            emailField.text = backend.rememberedEmail
        }
    }

    Connections {
        target: backend
        ignoreUnknownSignals: true
        function onRememberedEmailChanged() {
            if (backend && backend.hasRememberedEmail && !root.registerMode) {
                emailField.text = backend.rememberedEmail
            }
        }
    }
}
