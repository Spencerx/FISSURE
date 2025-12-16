#!/usr/bin/env python3
"""Artifact Management for FISSURE Operations
"""
import json
import os
import uuid
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Union, Tuple
import logging


@dataclass
class Artifact:
    """Represents an artifact created by an operation."""
    id: str
    operation_id: str
    name: str
    file_path: str
    artifact_type: str
    created_at: str
    file_size: int
    metadata: Dict[str, Any]
    modified_at: Optional[str] = None
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert artifact to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Artifact':
        """Create artifact from dictionary."""
        return cls(**data)


class ArtifactManager:
    """Manages artifacts on the sensor node."""
    
    def __init__(self, base_dir: Union[str, None] = None, logger: Union[logging.Logger, None] = None):
        """Initialize the artifact manager.
        
        Parameters
        ----------
        base_dir : Union[str, None], optional
            Base directory for storing artifacts, defaults to None to use "artifacts" directory in FISSURE root
        logger : Union[logging.Logger, None], optional
            Logger instance, defaults to None to use module logger
        """
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/artifacts"
        self.base_dir = base_dir
        self.logger = logger or logging.getLogger(__name__)
        self.index_file = os.path.join(base_dir, "index.json")
        
        # Ensure base directory exists
        os.makedirs(base_dir, exist_ok=True)
        
        # Load existing index
        self._artifacts = self._load_index()
    
    def _load_index(self) -> Dict[str, Artifact]:
        """Load the artifact index from disk.
        
        Returns
        -------
        Dict[str, Artifact]
            Mapping of artifact IDs to Artifact instances
        """
        if not os.path.exists(self.index_file):
            return {}
        try:
            with open(self.index_file, 'r') as f:
                data = json.load(f)
            return {aid: Artifact.from_dict(artifact_data) for aid, artifact_data in data.items()}
        except Exception as e:
            self.logger.error(f"Failed to load artifact index: {e}")
            return {}
    
    def _save_index(self) -> None:
        """Save the artifact index to disk."""
        try:
            data = {aid: artifact.to_dict() for aid, artifact in self._artifacts.items()}
            with open(self.index_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save artifact index: {e}")
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file.
        
        Parameters
        ----------
        file_path : str
            Path to the file

        Returns
        -------
        str
            SHA256 checksum of the file
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    def _get_operation_dir(self, operation_id: str) -> str:
        """Get the directory path for an operation's artifacts.

        Parameters
        ----------
        operation_id : str
            The operation ID

        Returns
        -------
        str
            The directory path for the operation's artifacts
        """
        return os.path.join(self.base_dir, operation_id)

    def create_operation_dir(self, operation_id: str) -> Tuple[str, str]:
        """Create directory for an operation's artifacts.

        Parameters
        ----------
        operation_id : str
            The operation ID

        Returns
        -------
        str, str
            The directory path for the operation's artifacts and the directory path for the operation's files
        """
        op_dir = self._get_operation_dir(operation_id)
        os.makedirs(op_dir, exist_ok=True)
        file_dir = os.path.join(op_dir, "files")
        os.makedirs(file_dir, exist_ok=True)
        return op_dir, file_dir

    def get_filename_for_artifact(self, operation_id: str, ext: str) -> str:
        """Generate a unique filename for an artifact file.

        Parameters
        ----------
        operation_id : str
            The operation ID
        ext : str
            The file extension

        Returns
        -------
        str
            Unique filename
        """
        _, file_dir = self.create_operation_dir(operation_id)
        return os.path.join(file_dir, str(uuid.uuid4()) + ext)

    def create_artifact(self, operation_id: str, file_path: str, name: str, artifact_type: str, metadata: Union[Dict[str, Any], None] = None) -> str:
        """Create a new artifact record.
        
        Parameters
        ----------
        operation_id : str
            ID of the operation that created the artifact
        file_path : str
            Path to the artifact file
        name : str
            Human-readable name for the artifact
        artifact_type : str
            Type of artifact (e.g., "log", "data", "image")
        metadata : Dict[str, Any], optional
            Additional metadata for the artifact
            
        Returns
        -------
        str
            The artifact ID
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Artifact file does not exist: {file_path}")
            return ""
        
        # Check if file_path basename is a UUID4
        basename = os.path.basename(file_path)
        basename_no_ext = os.path.splitext(basename)[0]
        try:
            parsed_uuid = uuid.UUID(basename_no_ext, version=4)
            # Verify it's actually a UUID4
            if parsed_uuid.version != 4:
                self.logger.debug(f"File basename '{basename_no_ext}' is a UUID but not version 4; will generate new UUID for artifact ID")
                artifact_id = str(uuid.uuid4())
            else:
                self.logger.info(f"File basename '{basename_no_ext}' is a valid UUID4 and will be used as artifact ID")
                artifact_id = basename_no_ext
        except ValueError:
            self.logger.debug(f"File basename '{basename_no_ext}' is not a valid UUID4; will generate new UUID for artifact ID")
            artifact_id = str(uuid.uuid4())
        
        # Create operation directory if it doesn't exist
        _ = self.create_operation_dir(operation_id)

        # Calculate file size and checksum
        file_size = os.path.getsize(file_path)
        checksum = self._calculate_checksum(file_path)

        # Create artifact record
        artifact = Artifact(
            id=artifact_id,
            operation_id=operation_id,
            name=name,
            file_path=file_path,
            artifact_type=artifact_type,
            created_at=datetime.now().isoformat(),
            file_size=file_size,
            checksum=checksum,
            metadata=metadata or {}
        )
        
        # Store in index
        self._artifacts[artifact_id] = artifact
        self._save_index()
        
        self.logger.info(f"Created artifact {artifact_id}: {name} ({artifact_type})")
        return artifact_id
    
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID.
        
        Parameters
        ----------
        artifact_id : str
            The artifact ID
            
        Returns
        -------
        Optional[Artifact]
            The artifact or None if not found
        """
        return self._artifacts.get(artifact_id)
    
    def get_artifacts_by_operation(self, operation_id: str) -> List[Artifact]:
        """Get all artifacts for a specific operation.
        
        Parameters
        ----------
        operation_id : str
            The operation ID
            
        Returns
        -------
        List[Artifact]
            List of artifacts for the operation
        """
        return [artifact for artifact in self._artifacts.values() 
                if artifact.operation_id == operation_id]
    
    def get_all_artifacts(self) -> List[Artifact]:
        """Get all artifacts.
        
        Returns
        -------
        List[Artifact]
            List of all artifacts
        """
        return list(self._artifacts.values())

    def update_artifact(self, artifact_id: str, file_path: Union[str, None] = None, metadata: Union[Dict[str, Any], None] = None) -> bool:
        """Update an artifact's metadata and optionally its file.
        
        Parameters
        ----------
        artifact_id : str
            The artifact ID
        file_path : Union[str, None], optional
            New file path for the artifact, by default None
        metadata : Union[Dict[str, Any], None], optional
            New metadata to merge into existing metadata, by default None
            
        Returns
        -------
        bool
            True if updated successfully, False otherwise
        """
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            self.logger.error(f"Artifact not found: {artifact_id}")
            return False
        
        if file_path:
            if not os.path.exists(file_path):
                self.logger.error(f"New artifact file does not exist: {file_path}")
                return False
            artifact.file_path = file_path
        else:
            file_path = artifact.file_path
        artifact.file_size = os.path.getsize(file_path)
        artifact.checksum = self._calculate_checksum(file_path)
        
        if metadata:
            artifact.metadata.update(metadata)

        artifact.modified_at = datetime.now().isoformat()
        
        self._save_index()
        
        self.logger.info(f"Updated artifact {artifact_id}: {artifact.name}")
        return True

    def delete_artifact(self, artifact_id: str) -> bool:
        """Delete an artifact and its file.
        
        Parameters
        ----------
        artifact_id : str
            The artifact ID
            
        Returns
        -------
        bool
            True if deleted successfully, False otherwise
        """
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            self.logger.error(f"Artifact not found: {artifact_id}")
            return False
        
        # Remove file if it exists
        if os.path.exists(artifact.file_path):
            try:
                os.remove(artifact.file_path)
            except Exception as e:
                self.logger.error(f"Failed to delete artifact file {artifact.file_path}: {e}")
                return False
        
        # Remove from index
        del self._artifacts[artifact_id]
        self._save_index()
        
        self.logger.info(f"Deleted artifact {artifact_id}: {artifact.name}")
        return True
    
    def cleanup_operation(self, operation_id: str) -> int:
        """Delete all artifacts for an operation.
        
        Parameters
        ----------
        operation_id : str
            The operation ID
            
        Returns
        -------
        int
            Number of artifacts deleted
        """
        artifacts = self.get_artifacts_by_operation(operation_id)
        deleted_count = 0
        
        for artifact in artifacts:
            if self.delete_artifact(artifact.id):
                deleted_count += 1
        
        # Remove operation directory if empty
        op_dir = self._get_operation_dir(operation_id)
        if os.path.exists(op_dir) and not os.listdir(op_dir):
            try:
                os.rmdir(op_dir)
            except Exception as e:
                self.logger.error(f"Failed to remove operation directory {op_dir}: {e}")
        
        return deleted_count


# Global artifact manager instance
_artifact_manager = None

def get_artifact_manager() -> ArtifactManager:
    """Get the global artifact manager instance.
    
    Returns
    -------
    ArtifactManager
        The global artifact manager instance
    """
    global _artifact_manager
    if _artifact_manager is None:
        _artifact_manager = ArtifactManager()
    return _artifact_manager

