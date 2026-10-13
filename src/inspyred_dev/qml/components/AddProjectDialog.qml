import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Popup {
    id: root
    objectName: 'addProjectDialog'

    property bool editMode: false
    property string originalName: ''

    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(420, parent ? parent.width - 32 : 420)
    modal: true
    focus: true
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    readonly property string sourceType: sourceTypeField.currentIndex === 0 ? 'folder' : 'github'
    readonly property string projectValue: sourceType === 'folder'
        ? projectLocation.text
        : repositoryUrlField.text
    readonly property bool hasLocation: projectValue.trim().length > 0
    readonly property var filteredRepositoryNames: {
        const query = repositorySearch.text.trim().toLowerCase()
        const matches = []
        for (let index = 0; index < GitHubAuth.repositoryNames.length; ++index) {
            const name = GitHubAuth.repositoryNames[index]
            if (query.length === 0 || name.toLowerCase().includes(query))
                matches.push(name)
        }
        return matches
    }
    readonly property bool validProject: editMode
        ? Projects.canEditProject(
            originalName,
            projectName.text,
            sourceType,
            projectValue
        )
        : Projects.canAddProject(projectName.text, sourceType, projectValue)

    function openForNewProject() {
        editMode = false
        originalName = ''
        repositorySearch.text = ''
        projectName.text = ''
        projectLocation.text = ''
        repositoryUrlField.text = ''
        repositoryField.currentIndex = -1
        sourceTypeField.currentIndex = 0
        open()
    }

    function openForEditProject() {
        if (Projects.activeProject === 'All projects')
            return
        editMode = true
        originalName = Projects.activeProject
        repositorySearch.text = ''
        projectName.text = Projects.activeProject
        sourceTypeField.currentIndex = Projects.activeProjectSource === 'github' ? 1 : 0
        projectLocation.text = sourceType === 'folder' ? Projects.activeProjectLocation : ''
        repositoryUrlField.text = sourceType === 'github' ? Projects.activeProjectLocation : ''
        repositoryField.currentIndex = -1
        if (sourceType === 'github')
            loadGitHubRepositories()
        open()
    }

    function saveProject() {
        let saved = false
        const repositoryIndex = GitHubAuth.repositoryNames.indexOf(repositoryField.currentText)
        if (sourceType === 'github'
                && repositoryIndex >= 0
                && projectValue === GitHubAuth.repositoryUrlAt(repositoryIndex)) {
            if (editMode) {
                saved = Projects.editGitHubProject(
                    originalName,
                    projectName.text,
                    projectValue,
                    GitHubAuth.repositoryIdAt(repositoryIndex),
                    GitHubAuth.repositoryDefaultBranchAt(repositoryIndex)
                )
            } else {
                saved = Projects.addGitHubProject(
                    projectName.text,
                    projectValue,
                    GitHubAuth.repositoryIdAt(repositoryIndex),
                    GitHubAuth.repositoryDefaultBranchAt(repositoryIndex)
                )
            }
        } else {
            saved = editMode
                ? Projects.editProject(
                    originalName,
                    projectName.text,
                    sourceType,
                    projectValue
                )
                : Projects.addProject(projectName.text, sourceType, projectValue)
        }
        if (saved)
            close()
    }

    function loadGitHubRepositories() {
        if (root.sourceType === 'github') {
            const exclusions = root.editMode
                ? Projects.githubRepositoryUrlsExcept(root.originalName)
                : Projects.githubRepositoryUrls
            GitHubAuth.loadRepositories(exclusions)
        }
    }

    function selectFirstFilteredRepository() {
        if (filteredRepositoryNames.length === 0) {
            repositoryField.currentIndex = -1
            return
        }
        repositoryField.currentIndex = 0
        const repositoryIndex = GitHubAuth.repositoryNames.indexOf(filteredRepositoryNames[0])
        if (repositoryIndex >= 0)
            repositoryUrlField.text = GitHubAuth.repositoryUrlAt(repositoryIndex)
    }

    function selectRepositoryUrl(repositoryUrl) {
        for (let index = 0; index < GitHubAuth.repositoryNames.length; ++index) {
            if (GitHubAuth.repositoryUrlAt(index) !== repositoryUrl)
                continue
            const filteredIndex = filteredRepositoryNames.indexOf(
                GitHubAuth.repositoryNames[index]
            )
            repositoryField.currentIndex = filteredIndex
            return filteredIndex >= 0
        }
        repositoryField.currentIndex = -1
        return false
    }

    onOpened: projectLocation.forceActiveFocus()

    Connections {
        target: GitHubAuth

        function onRepositoriesChanged() {
            if (root.sourceType === 'github'
                    && !GitHubAuth.repositoriesLoading
                    && GitHubAuth.repositoryNames.length > 0) {
                if (root.editMode)
                    root.selectRepositoryUrl(repositoryUrlField.text)
                else
                    root.selectFirstFilteredRepository()
            }
        }
    }

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
                    text: root.editMode ? 'Edit project' : 'Add project'
                    color: Theme.textPrimary
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }

                Text {
                    Layout.fillWidth: true
                    text: root.editMode
                        ? 'Update this inbox or connect it to GitHub.'
                        : 'Create a separate inbox for related observations.'
                    color: Theme.textSecondary
                    font.pixelSize: 12
                    elide: Text.ElideRight
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
                onActivated: {
                    projectLocation.text = ''
                    repositoryUrlField.text = ''
                    repositorySearch.text = ''
                    if (root.sourceType === 'github')
                        root.loadGitHubRepositories()
                }
            }

            Text {
                Layout.topMargin: 5
                visible: root.sourceType === 'folder'
                text: 'Folder'
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
                    visible: root.sourceType === 'folder'
                    placeholderText: 'Choose or enter a folder path'
                    helpId: 'add-project'
                    onAccepted: root.saveProject()
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
                visible: root.sourceType === 'github'
                text: 'Available repositories'
                color: Theme.textSecondary
                font.pixelSize: 12
            }

            InspyredTextField {
                id: repositorySearch
                objectName: 'githubRepositorySearch'
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                visible: root.sourceType === 'github'
                    && GitHubAuth.repositoryNames.length > 0
                placeholderText: 'Search by owner or repository name'
                helpText: 'Filter the repositories available to this GitHub App.'
                onTextEdited: root.selectFirstFilteredRepository()
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                visible: root.sourceType === 'github'
                spacing: 8

                InspyredComboBox {
                    id: repositoryField
                    objectName: 'githubRepositoryField'
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    visible: root.filteredRepositoryNames.length > 0
                    model: root.filteredRepositoryNames
                    helpText: 'Repositories accessible to GitHub that are not already projects'
                    onActivated: {
                        const repositoryIndex = GitHubAuth.repositoryNames.indexOf(currentText)
                        if (repositoryIndex >= 0)
                            repositoryUrlField.text = GitHubAuth.repositoryUrlAt(repositoryIndex)
                    }
                }

                Text {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    visible: GitHubAuth.repositoriesLoading
                    text: 'Loading repositories…'
                    color: Theme.textSecondary
                    font.pixelSize: 12
                }

                InspyredButton {
                    iconName: 'refresh'
                    iconOnly: true
                    text: 'Refresh'
                    compact: true
                    enabled: GitHubAuth.signedIn && !GitHubAuth.repositoriesLoading
                    tooltip: 'Refresh GitHub repositories'
                    onClicked: root.loadGitHubRepositories()
                }
            }

            Text {
                Layout.fillWidth: true
                visible: root.sourceType === 'github'
                    && GitHubAuth.repositoryNames.length > 0
                    && root.filteredRepositoryNames.length === 0
                text: 'No repositories match this search.'
                color: Theme.textSecondary
                font.pixelSize: 12
            }

            Text {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                visible: root.sourceType === 'github'
                    && !GitHubAuth.repositoriesLoading
                    && GitHubAuth.repositoryNames.length === 0
                text: GitHubAuth.repositoriesError.length > 0
                    ? GitHubAuth.repositoriesError
                    : 'No additional repositories are available. The app may need repository access on GitHub.'
                color: GitHubAuth.repositoriesError.length > 0 ? Theme.danger : Theme.textSecondary
                font.pixelSize: 12
                wrapMode: Text.Wrap
            }

            InspyredButton {
                Layout.alignment: Qt.AlignRight
                visible: root.sourceType === 'github'
                    && GitHubAuth.signedIn
                    && !GitHubAuth.repositoriesLoading
                    && GitHubAuth.repositoryNames.length === 0
                text: 'Manage repository access'
                forceLabel: true
                compact: true
                tooltip: 'Open your GitHub App settings to install the app or change repository access'
                onClicked: GitHubAuth.openGitHubAppSettings()
            }

            Text {
                Layout.topMargin: 5
                visible: root.sourceType === 'github'
                text: 'Repository link (manual fallback)'
                color: Theme.textSecondary
                font.pixelSize: 12
            }

            InspyredTextField {
                id: repositoryUrlField
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                visible: root.sourceType === 'github'
                placeholderText: 'https://github.com/owner/repository'
                helpId: 'add-project'
                onAccepted: root.saveProject()
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
                enabled: !root.editMode || root.originalName !== 'Inspyred Dev'
                helpId: 'add-project'
                onAccepted: root.saveProject()
            }

            Text {
                visible: root.hasLocation && !root.validProject
                text: root.sourceType === 'folder'
                    ? 'Choose an existing folder that is not already a project.'
                    : 'Choose a repository that is not already a project, or enter its GitHub link.'
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
                text: root.editMode ? 'Save changes' : 'Add project'
                iconName: root.editMode ? 'edit' : 'add'
                forceLabel: true
                compact: true
                accent: true
                helpId: 'add-project'
                enabled: root.validProject
                onClicked: root.saveProject()
            }
        }
    }
}
