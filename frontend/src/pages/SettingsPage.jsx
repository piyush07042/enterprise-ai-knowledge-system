import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./SettingsPage.css";

export default function SettingsPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [selectedProfileFile, setSelectedProfileFile] = useState(null);
  const [selectedProfilePreview, setSelectedProfilePreview] = useState(null);
  const [profilePictureSrc, setProfilePictureSrc] = useState(null);
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploadingPicture, setUploadingPicture] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSettings();
  }, []);

  useEffect(() => {
    return () => {
      if (selectedProfilePreview) {
        URL.revokeObjectURL(selectedProfilePreview);
      }
    };
  }, [selectedProfilePreview]);

  useEffect(() => {
    return () => {
      if (profilePictureSrc) {
        URL.revokeObjectURL(profilePictureSrc);
      }
    };
  }, [profilePictureSrc]);

  const loadProfilePicture = async (profilePictureUrl) => {
    try {
      if (profilePictureSrc) {
        URL.revokeObjectURL(profilePictureSrc);
      }

      const token = localStorage.getItem("token");
      const res = await api.get(profilePictureUrl, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        responseType: "blob",
      });

      const objectUrl = URL.createObjectURL(res.data);
      setProfilePictureSrc(objectUrl);
    } catch (err) {
      console.log(err);
      setProfilePictureSrc(null);
    }
  };

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await api.get("/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setUsername(res.data.username || "");
      setEmail(res.data.email || "");

      if (res.data.profile_picture_url) {
        await loadProfilePicture(res.data.profile_picture_url);
      } else {
        setProfilePictureSrc(null);
      }
    } catch (err) {
      console.log(err);
    }
  };

  const handleProfilePictureChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    if (!["image/jpeg", "image/png"].includes(file.type)) {
      setMessage("Use a JPG, JPEG, or PNG image.");
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      setMessage("Profile picture must be 2 MB or smaller.");
      return;
    }

    if (selectedProfilePreview) {
      URL.revokeObjectURL(selectedProfilePreview);
    }

    const previewUrl = URL.createObjectURL(file);
    setSelectedProfileFile(file);
    setSelectedProfilePreview(previewUrl);
    setMessage("");
  };

  const uploadProfilePicture = async () => {
    if (!selectedProfileFile) {
      setMessage("Choose an image first.");
      return;
    }

    try {
      setUploadingPicture(true);

      const token = localStorage.getItem("token");
      const formData = new FormData();
      formData.append("file", selectedProfileFile);

      const res = await api.post("/upload-profile-picture", formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      });

      setMessage(res.data.message || "Profile picture uploaded successfully.");
      setSelectedProfileFile(null);

      if (selectedProfilePreview) {
        URL.revokeObjectURL(selectedProfilePreview);
        setSelectedProfilePreview(null);
      }

      await fetchSettings();
    } catch (err) {
      setMessage(err.response?.data?.detail || "Profile picture upload failed.");
    } finally {
      setUploadingPicture(false);
    }
  };

  const saveChanges = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem("token");

      const res = await api.put(
        "/settings",
        {
          username,
          email,
          password,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (res?.data?.access_token) {
        localStorage.setItem("token", res.data.access_token);
      }

      localStorage.setItem("email", email);

      setMessage("Settings updated successfully.");
      navigate("/dashboard");
    } catch (err) {
      setMessage(err.response?.data?.detail || "Update failed.");
    } finally {
      setSaving(false);
    }
  };

  const avatarLabel = username ? username.charAt(0).toUpperCase() : "U";
  const avatarSource = selectedProfilePreview || profilePictureSrc;

  return (
    <div className="settings-page">
      <div className="settings-shell">
        <div className="settings-topbar">
          <button className="settings-back" onClick={() => navigate("/dashboard")}>
            ← Back
          </button>

          <div>
            <p className="settings-eyebrow">Account</p>
            <h1>Settings</h1>
          </div>
        </div>

        {message && <div className="settings-alert">{message}</div>}

        <div className="settings-grid">
          <section className="settings-card settings-profile-card">
            <div className="settings-card-header">
              <div>
                <p className="settings-card-label">Profile picture</p>
                <h2>Upload a photo</h2>
              </div>
            </div>

            <div className="profile-preview">
              {avatarSource ? (
                <img src={avatarSource} alt="Profile preview" />
              ) : (
                <span>{avatarLabel}</span>
              )}
            </div>

            <p className="profile-hint">
              JPG, JPEG, or PNG. Maximum file size: 2 MB.
            </p>

            <input
              type="file"
              accept="image/jpeg,image/png"
              onChange={handleProfilePictureChange}
              className="profile-input"
            />

            <button
              className="upload-btn"
              onClick={uploadProfilePicture}
              disabled={uploadingPicture}
            >
              {uploadingPicture ? "Uploading..." : "Upload Picture"}
            </button>
          </section>

          <section className="settings-card settings-form-card">
            <div className="settings-card-header">
              <div>
                <p className="settings-card-label">Account details</p>
                <h2>Update your profile</h2>
              </div>
            </div>

            <div className="settings-field">
              <label>Username</label>
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
              />
            </div>

            <div className="settings-field">
              <label>Email</label>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
              />
            </div>

            <div className="settings-field">
              <label>New Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Leave blank to keep current password"
              />
            </div>

            <button className="save-btn" onClick={saveChanges} disabled={saving}>
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}