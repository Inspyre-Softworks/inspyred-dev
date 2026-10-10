import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: root
    objectName: 'settingsWindow'

    required property Window targetWindow

    visible: false
    width: 520
    height: 640
    minimumWidth: 440
    minimumHeight: 560
    title: 'Settings'
    color: Theme.background
    flags: Qt.Window | Qt.FramelessWindowHint
    transientParent: targetWindow

    header: CustomTitleBar {
        targetWindow: root
    }

    onVisibleChanged: {
        if (visible) {
            x = targetWindow.x + Math.round((targetWindow.width - width) / 2)
            y = targetWindow.y + Math.round((targetWindow.height - height) / 2)
        }
    }

    function showSettings() {
        show()
        raise()
        requestActivate()
    }

    component SettingsSwitch: Switch {
        id: control

        implicitWidth: 48
        implicitHeight: 28
        padding: 0

        contentItem: Item {}

        indicator: Rectangle {
            implicitWidth: 48
            implicitHeight: 28
            radius: 14
            color: control.checked ? Theme.accent : Theme.surfaceAlt
            border.color: control.checked ? Theme.accentHover : Theme.border

            Rectangle {
                width: 20
                height: 20
                y: 4
                x: control.checked ? parent.width - width - 4 : 4
                radius: 10
                color: '#FFFFFF'

                Behavior on x {
                    NumberAnimation { duration: 120; easing.type: Easing.OutCubic }
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0; color: Theme.backgroundAlt }
            GradientStop { position: 1; color: Theme.background }
        }
    }

    ScrollView {
        objectName: 'settingsScroll'
        anchors.fill: parent
        anchors.margins: 24
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: root.width - 48
            spacing: 16

            Text {
                text: 'Settings'
                color: Theme.textPrimary
                font.pixelSize: 28
                font.weight: Font.Bold
            }

            Text {
                text: 'Tune how Inspyred Dev looks and captures observations.'
                color: Theme.textSecondary
                font.pixelSize: 14
                Layout.bottomMargin: 4
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: appearanceLayout.implicitHeight + 32
                radius: 14
                color: Theme.surface
                border.color: Theme.border

                ColumnLayout {
                    id: appearanceLayout
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 10

                    Text {
                        text: 'Appearance'
                        color: Theme.textPrimary
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }

                    Text {
                        text: 'Theme'
                        color: Theme.textSecondary
                        font.pixelSize: 12
                    }

                    InspyredComboBox {
                        Layout.fillWidth: true
                        model: ['System', 'Light', 'Dark']
                        currentIndex: AppSettings.themeMode === 'system' ? 0 : (AppSettings.themeMode === 'light' ? 1 : 2)
                        helpId: 'appearance-theme'
                        onActivated: function(index) {
                            AppSettings.setThemeMode(['system', 'light', 'dark'][index])
                        }
                    }

                    Text {
                        text: 'Navigation labels'
                        color: Theme.textSecondary
                        font.pixelSize: 12
                        Layout.topMargin: 2
                    }

                    InspyredComboBox {
                        Layout.fillWidth: true
                        model: ['Icons + text', 'Icons only']
                        currentIndex: AppSettings.labelMode === 'icons_text' ? 0 : 1
                        helpId: 'appearance-labels'
                        onActivated: function(index) {
                            AppSettings.setLabelMode(index === 0 ? 'icons_text' : 'icons_only')
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: captureLayout.implicitHeight + 32
                radius: 14
                color: Theme.surface
                border.color: Theme.border

                ColumnLayout {
                    id: captureLayout
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    Text {
                        text: 'Quick capture'
                        color: Theme.textPrimary
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3

                            Text {
                                text: 'Global shortcut'
                                color: Theme.textPrimary
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                            }

                            Text {
                                Layout.fillWidth: true
                                text: 'Open Quick Capture from any app with Ctrl+Shift+N.'
                                color: Theme.textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.Wrap
                            }
                        }

                        SettingsSwitch {
                            checked: AppSettings.globalCaptureEnabled
                            Accessible.name: 'Enable global quick capture shortcut'
                            onToggled: AppSettings.setGlobalCaptureEnabled(checked)
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: Theme.border
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3

                            Text {
                                text: 'Capture active window'
                                color: Theme.textPrimary
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                            }

                            Text {
                                Layout.fillWidth: true
                                text: 'Attach a screenshot of the foreground window when the shortcut is used.'
                                color: Theme.textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.Wrap
                            }
                        }

                        SettingsSwitch {
                            checked: AppSettings.captureScreenshots
                            enabled: AppSettings.globalCaptureEnabled
                            Accessible.name: 'Capture the active window with quick capture'
                            onToggled: AppSettings.setCaptureScreenshots(checked)
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: shortcutStatus.implicitHeight + 20
                        radius: 10
                        color: Theme.surfaceAlt
                        border.color: QuickCapture.lastError.length > 0 ? Theme.danger : Theme.border

                        Text {
                            id: shortcutStatus
                            anchors.fill: parent
                            anchors.margins: 10
                            text: QuickCapture.lastError.length > 0
                                ? QuickCapture.lastError
                                : (AppSettings.globalCaptureEnabled
                                    ? 'Ctrl+Shift+N is ready.'
                                    : 'Global quick capture is turned off.')
                            color: QuickCapture.lastError.length > 0
                                ? Theme.danger
                                : (QuickCapture.hotkeyRegistered ? Theme.success : Theme.textSecondary)
                            font.pixelSize: 12
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }

            Rectangle {
                objectName: 'githubCard'
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                Layout.maximumWidth: parent.width
                implicitHeight: githubLayout.implicitHeight + 32
                radius: 14
                color: Theme.surface
                border.color: Theme.border

                ColumnLayout {
                    id: githubLayout
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    Text {
                        text: 'GitHub'
                        color: Theme.textPrimary
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }

                    Text {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        visible: !GitHubAuth.signedIn && GitHubAuth.status !== 'waiting_for_authorization'
                        text: GitHubAuth.configured
                            ? 'Connect your GitHub account to validate repositories and prepare issue and project synchronization.'
                            : 'Set up GitHub access here, then sign in through your browser.'
                        color: Theme.textSecondary
                        font.pixelSize: 12
                        wrapMode: Text.Wrap
                    }

                    ColumnLayout {
                        objectName: 'githubSetup'
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        visible: !GitHubAuth.configured
                        spacing: 10

                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: setupSteps.implicitHeight + 24
                            radius: 10
                            color: Theme.surfaceAlt
                            border.color: Theme.border

                            ColumnLayout {
                                id: setupSteps
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 6

                                Text {
                                    Layout.fillWidth: true
                                    text: '1. Create a GitHub App for Inspyred Dev.'
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    font.weight: Font.DemiBold
                                    wrapMode: Text.Wrap
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: '2. In its settings, enable Device Flow.'
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    font.weight: Font.DemiBold
                                    wrapMode: Text.Wrap
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: '3. Copy the public Client ID and paste it below.'
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    font.weight: Font.DemiBold
                                    wrapMode: Text.Wrap
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: 'No client secret or private key is needed.'
                                    color: Theme.textSecondary
                                    font.pixelSize: 11
                                    wrapMode: Text.Wrap
                                }
                            }
                        }

                        InspyredButton {
                            text: 'Create GitHub App'
                            forceLabel: true
                            compact: true
                            tooltip: 'Open GitHub\'s new app form in your browser'
                            onClicked: GitHubAuth.openGitHubAppCreation()
                        }

                        InspyredTextField {
                            id: githubClientIdField
                            objectName: 'githubClientIdField'
                            Layout.fillWidth: true
                            placeholderText: 'GitHub App Client ID'
                            helpText: 'The public Client ID from the GitHub App settings page'
                            onAccepted: GitHubAuth.configureAndSignIn(text)
                        }

                        InspyredButton {
                            objectName: 'githubConfigureButton'
                            Layout.alignment: Qt.AlignRight
                            text: 'Save and sign in'
                            forceLabel: true
                            accent: true
                            enabled: githubClientIdField.text.trim().length >= 10
                            onClicked: GitHubAuth.configureAndSignIn(githubClientIdField.text)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        visible: GitHubAuth.signedIn
                        spacing: 12

                        Rectangle {
                            Layout.preferredWidth: 44
                            Layout.preferredHeight: 44
                            radius: 22
                            color: Theme.surfaceAlt
                            border.color: Theme.border
                            clip: true

                            Image {
                                anchors.fill: parent
                                source: GitHubAuth.avatarUrl
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            spacing: 2

                            Text {
                                text: GitHubAuth.displayName
                                color: Theme.textPrimary
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                            }

                            Text {
                                text: '@' + GitHubAuth.login
                                color: Theme.textSecondary
                                font.pixelSize: 12
                            }
                        }

                        InspyredButton {
                            text: 'Sign out'
                            forceLabel: true
                            compact: true
                            tooltip: 'Remove GitHub credentials from this device'
                            onClicked: GitHubAuth.signOut()
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        visible: GitHubAuth.status === 'waiting_for_authorization'
                        spacing: 8

                        Text {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            text: 'Enter this code on GitHub to finish signing in:'
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            wrapMode: Text.Wrap
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 52
                            radius: 10
                            color: Theme.surfaceAlt
                            border.color: Theme.cyan

                            Text {
                                anchors.centerIn: parent
                                text: GitHubAuth.userCode
                                color: Theme.textPrimary
                                font.pixelSize: 22
                                font.weight: Font.Bold
                                font.letterSpacing: 2
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            spacing: 8

                            InspyredButton {
                                text: 'Copy code'
                                forceLabel: true
                                compact: true
                                tooltip: 'Copy the GitHub device code'
                                onClicked: GitHubAuth.copyUserCode()
                            }

                            Item { Layout.fillWidth: true }

                            InspyredButton {
                                text: 'Open GitHub'
                                forceLabel: true
                                compact: true
                                accent: true
                                helpId: 'github-sign-in'
                                onClicked: GitHubAuth.openVerificationPage()
                            }
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        visible: GitHubAuth.errorMessage.length > 0
                        text: GitHubAuth.errorMessage
                        color: Theme.danger
                        font.pixelSize: 12
                        wrapMode: Text.Wrap
                    }

                    RowLayout {
                        objectName: 'githubSignInRow'
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        visible: !GitHubAuth.signedIn
                            && GitHubAuth.status !== 'waiting_for_authorization'
                            && GitHubAuth.configured
                        spacing: 10

                        Text {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            visible: GitHubAuth.busy
                            text: GitHubAuth.status === 'checking_account'
                                ? 'Checking saved GitHub account…'
                                : (GitHubAuth.status === 'refreshing'
                                    ? 'Refreshing GitHub session…'
                                    : 'Starting GitHub sign-in…')
                            color: Theme.textSecondary
                            font.pixelSize: 12
                        }

                        Item {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            visible: !GitHubAuth.busy
                        }

                        InspyredButton {
                            objectName: 'githubSignInButton'
                            text: 'Sign in with GitHub'
                            forceLabel: true
                            accent: true
                            helpId: 'github-sign-in'
                            enabled: GitHubAuth.configured && !GitHubAuth.busy
                            onClicked: GitHubAuth.signIn()
                        }
                    }
                }
            }

            Item { Layout.preferredHeight: 8 }
        }
    }

    WindowResizeHandles {
        anchors.fill: parent
        targetWindow: root
        z: 1000
    }
}
