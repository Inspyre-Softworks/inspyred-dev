import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: root
    objectName: 'batchIssueDialog'

    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(460, parent ? parent.width - 32 : 460)
    modal: true
    focus: true
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    readonly property string mode: ['one', 'keywords', 'individual'][modeField.currentIndex]
    readonly property bool validBatch: Observations.selectedGithubIssueEligible
        && GitHubAuth.signedIn
        && GitHubAuth.issueCreationObservationId === 0
        && (mode !== 'keywords' || keywordField.text.trim().length > 0)

    function openForSelection() {
        modeField.currentIndex = 0
        keywordField.text = ''
        open()
    }

    background: Rectangle {
        color: Theme.surfaceRaised
        border.color: Theme.borderStrong
        border.width: 1
        radius: 16
    }

    contentItem: ColumnLayout {
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 16
            Layout.topMargin: 18
            spacing: 12

            Rectangle {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                radius: 10
                color: Theme.surfaceAlt
                border.color: Theme.border

                InspyredIcon {
                    anchors.centerIn: parent
                    width: 20
                    height: 20
                    name: 'layers'
                    color: Theme.cyan
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Text {
                    text: 'Create GitHub issues'
                    color: Theme.textPrimary
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }

                Text {
                    text: Observations.selectedCount + ' selected note(s) in one repository'
                    color: Theme.textSecondary
                    font.pixelSize: 12
                }
            }

            InspyredButton {
                iconName: 'close'
                iconOnly: true
                text: 'Close'
                compact: true
                tooltip: 'Close'
                onClicked: root.close()
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            spacing: 8

            Text {
                text: 'Issue strategy'
                color: Theme.textSecondary
                font.pixelSize: 12
            }

            InspyredComboBox {
                id: modeField
                Layout.fillWidth: true
                model: [
                    'One combined issue',
                    'Group into issues by keywords',
                    'One issue per note'
                ]
                helpText: 'Choose how the selected notes become issues in this repository.'
            }

            Text {
                Layout.fillWidth: true
                text: mode === 'one'
                    ? 'All selected notes become sections in one GitHub issue.'
                    : (mode === 'keywords'
                        ? 'Each note is assigned to the first matching keyword. Unmatched notes become one Other issue.'
                        : 'Each selected note becomes its own GitHub issue.')
                color: Theme.textSecondary
                font.pixelSize: 12
                wrapMode: Text.Wrap
            }

            Text {
                visible: mode === 'keywords'
                Layout.topMargin: 4
                text: 'Keywords, in matching order'
                color: Theme.textSecondary
                font.pixelSize: 12
            }

            InspyredTextField {
                id: keywordField
                visible: mode === 'keywords'
                Layout.fillWidth: true
                placeholderText: 'authentication, settings, mobile'
                helpText: 'Separate keywords with commas. Matching ignores capitalization.'
            }

            Text {
                visible: !GitHubAuth.signedIn
                Layout.fillWidth: true
                text: 'Sign in with GitHub in Settings before creating issues.'
                color: Theme.danger
                font.pixelSize: 12
                wrapMode: Text.Wrap
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            Layout.bottomMargin: 18
            spacing: 10

            Item { Layout.fillWidth: true }

            InspyredButton {
                text: 'Cancel'
                forceLabel: true
                compact: true
                onClicked: root.close()
            }

            InspyredButton {
                text: mode === 'one' ? 'Create issue' : 'Create issues'
                forceLabel: true
                compact: true
                accent: true
                enabled: root.validBatch
                onClicked: {
                    const requests = Observations.buildGithubIssueBatch(
                        root.mode,
                        keywordField.text
                    )
                    if (requests.length > 0) {
                        GitHubAuth.createIssueBatch(requests)
                        root.close()
                    }
                }
            }
        }
    }
}
