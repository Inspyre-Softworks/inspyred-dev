import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Popup {
    id: root
    objectName: 'addProjectDialog'

    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(420, parent ? parent.width - 32 : 420)
    modal: true
    focus: true
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    readonly property string sourceType: sourceTypeField.currentIndex === 0 ? 'folder' : 'github'
    readonly property bool hasLocation: projectLocation.text.trim().length > 0
    readonly property bool validProject: Projects.canAddProject(
        projectName.text,
        sourceType,
        projectLocation.text
    )

    function openForNewProject() {
        projectName.text = ''
        projectLocation.text = ''
        sourceTypeField.currentIndex = 0
        open()
    }

    function createProject() {
        if (Projects.addProject(projectName.text, sourceType, projectLocation.text))
            close()
    }

    onOpened: projectLocation.forceActiveFocus()

    FolderDialog {
        id: folderDialog
        title: 'Choose project folder'
        onAccepted: {
            projectLocation.text = Projects.localPathFromUrl(selectedFolder.toString())
            projectName.forceActiveFocus()
        }
    }

    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: 'opacity'; from: 0; to: 1; duration: 130 }
            NumberAnimation { property: 'scale'; from: 0.98; to: 1; duration: 130 }
        }
    }

    exit: Transition {
        NumberAnimation { property: 'opacity'; from: 1; to: 0; duration: 90 }
    }

    background: Rectangle {
        color: Theme.surfaceRaised
        border.color: Theme.borderStrong
        border.width: 1
        radius: 16
    }

    contentItem: ColumnLayout {
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
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
                Layout.minimumWidth: 0
                spacing: 2

                Text {
                    text: 'Add project'
                    color: Theme.textPrimary
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }

                Text {
                    Layout.fillWidth: true
                    text: 'Create a separate inbox for related observations.'
                    color: Theme.textSecondary
                    font.pixelSize: 12
                    elide: Text.ElideRight
                }
            }

            InspyredButton {
                iconName: 'close'
                iconOnly: true
                compact: true
                tooltip: 'Close'
                onClicked: root.close()
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            spacing: 7

            Text {
                text: 'Project source'
                color: Theme.textSecondary
                font.pixelSize: 12
            }

            InspyredComboBox {
                id: sourceTypeField
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                model: ['Local folder', 'GitHub repository']
                helpId: 'add-project'
                onActivated: projectLocation.text = ''
            }

            Text {
                Layout.topMargin: 5
                text: root.sourceType === 'folder' ? 'Folder' : 'GitHub repository link'
                color: Theme.textSecondary
                font.pixelSize: 12
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                spacing: 8

                InspyredTextField {
                    id: projectLocation
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    placeholderText: root.sourceType === 'folder'
                        ? 'Choose or enter a folder path'
                        : 'https://github.com/owner/repository'
                    helpId: 'add-project'
                    onAccepted: root.createProject()
                }

                InspyredButton {
                    visible: root.sourceType === 'folder'
                    text: 'Browse'
                    forceLabel: true
                    compact: true
                    tooltip: 'Choose a local project folder'
                    onClicked: folderDialog.open()
                }
            }

            Text {
                Layout.topMargin: 5
                text: 'Display name (optional)'
                color: Theme.textSecondary
                font.pixelSize: 12
            }

            InspyredTextField {
                id: projectName
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                placeholderText: 'Defaults to the folder or repository name'
                maximumLength: 120
                helpId: 'add-project'
                onAccepted: root.createProject()
            }

            Text {
                visible: root.hasLocation && !root.validProject
                text: root.sourceType === 'folder'
                    ? 'Choose an existing folder that is not already a project.'
                    : 'Enter a unique GitHub repository link, such as https://github.com/owner/repo.'
                color: Theme.danger
                font.pixelSize: 12
                Layout.fillWidth: true
                wrapMode: Text.Wrap
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            Layout.bottomMargin: 18
            spacing: 10

            Item { Layout.fillWidth: true }

            InspyredButton {
                text: 'Cancel'
                forceLabel: true
                compact: true
                tooltip: 'Close without creating a project'
                onClicked: root.close()
            }

            InspyredButton {
                text: 'Add project'
                iconName: 'add'
                forceLabel: true
                compact: true
                accent: true
                helpId: 'add-project'
                enabled: root.validProject
                onClicked: root.createProject()
            }
        }
    }
}
