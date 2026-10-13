import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../qml/components" as Components

Rectangle {
    id: root
    objectName: 'githubCard'

    Layout.fillWidth: true
    implicitHeight: content.implicitHeight + 32
    radius: 14
    color: Theme.surface
    border.color: Theme.border

    ColumnLayout {
        id: content
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
            visible: !GitHubAuth.signedIn
                && GitHubAuth.status !== 'waiting_for_authorization'
            text: GitHubAuth.configured
                ? 'Connect your GitHub account to browse repositories and publish issues.'
                : 'Set up GitHub access here, then sign in through your browser.'
            color: Theme.textSecondary
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }

        ColumnLayout {
            objectName: 'githubSetup'
            Layout.fillWidth: true
            visible: !GitHubAuth.configured
            spacing: 10

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: setupText.implicitHeight + 24
                radius: 10
                color: Theme.surfaceAlt
                border.color: Theme.border

                Text {
                    id: setupText
                    anchors.fill: parent
                    anchors.margins: 12
                    text: '1. Create a GitHub App for Inspyred Dev.\n'
                        + '2. Enable Device Flow and grant Issues read/write access.\n'
                        + '3. Install it on the repositories you want available.\n'
                        + '4. Paste its public Client ID below.\n\n'
                        + 'No client secret or private key is needed.'
                    color: Theme.textPrimary
                    font.pixelSize: 12
                    lineHeight: 1.25
                    wrapMode: Text.Wrap
                }
            }

            Components.InspyredButton {
                text: 'Create GitHub App'
                forceLabel: true
                compact: true
                tooltip: 'Open GitHub\'s new app form in your browser'
                onClicked: GitHubAuth.openGitHubAppCreation()
            }

            Components.InspyredTextField {
                id: githubClientIdField
                objectName: 'githubClientIdField'
                Layout.fillWidth: true
                placeholderText: 'GitHub App Client ID'
                helpText: 'The public Client ID from the GitHub App settings page'
                onAccepted: GitHubAuth.configureAndSignIn(text)
            }

            Components.InspyredButton {
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

            Components.InspyredButton {
                text: 'Sign out'
                forceLabel: true
                compact: true
                tooltip: 'Remove GitHub credentials from this device'
                onClicked: GitHubAuth.signOut()
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            visible: GitHubAuth.status === 'waiting_for_authorization'
            spacing: 8

            Text {
                Layout.fillWidth: true
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

                Components.InspyredButton {
                    text: 'Copy code'
                    forceLabel: true
                    compact: true
                    onClicked: GitHubAuth.copyUserCode()
                }

                Item { Layout.fillWidth: true }

                Components.InspyredButton {
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
            visible: GitHubAuth.errorMessage.length > 0
            text: GitHubAuth.errorMessage
            color: Theme.danger
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }

        RowLayout {
            objectName: 'githubSignInRow'
            Layout.fillWidth: true
            visible: !GitHubAuth.signedIn
                && GitHubAuth.status !== 'waiting_for_authorization'
                && GitHubAuth.configured

            Text {
                Layout.fillWidth: true
                visible: GitHubAuth.busy
                text: GitHubAuth.status === 'checking_account'
                    ? 'Checking saved GitHub account…'
                    : (GitHubAuth.status === 'refreshing'
                        ? 'Refreshing GitHub session…'
                        : 'Starting GitHub sign-in…')
                color: Theme.textSecondary
                font.pixelSize: 12
            }

            Item { Layout.fillWidth: true; visible: !GitHubAuth.busy }

            Components.InspyredButton {
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
