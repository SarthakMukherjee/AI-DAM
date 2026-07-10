import React, { useState, useEffect } from "react";
import api from "../../api/axios";
import Layout from "../../components/common/Layout";
import "../../styles/admindashboard.css";

const TaxonomyManagement = () => {
  const [categories, setCategories] = useState([]);
  const [tags, setTags] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);

  // Form states
  const [catName, setCatName] = useState("");
  const [catDesc, setCatDesc] = useState("");
  const [tagName, setTagName] = useState("");

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    if (selectedCategory) {
      fetchTags(selectedCategory.id);
    } else {
      setTags([]);
    }
  }, [selectedCategory]);

  const fetchCategories = async () => {
    try {
      const res = await api.get("/taxonomy/categories");
      setCategories(res.data);
    } catch (err) {
      console.error("Failed to load categories", err);
    }
  };

  const fetchTags = async (categoryId) => {
    try {
      const res = await api.get(`/taxonomy/tags?category_id=${categoryId}`);
      setTags(res.data);
    } catch (err) {
      console.error("Failed to load tags", err);
    }
  };

  const handleCreateCategory = async (e) => {
    e.preventDefault();
    if (!catName) return;
    try {
      await api.post("/taxonomy/categories", { name: catName, description: catDesc });
      setCatName("");
      setCatDesc("");
      fetchCategories();
    } catch (err) {
      alert("Failed to create category: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteCategory = async (id) => {
    if (!window.confirm("Delete category and all its tags?")) return;
    try {
      await api.delete(`/taxonomy/categories/${id}`);
      if (selectedCategory?.id === id) setSelectedCategory(null);
      fetchCategories();
    } catch (err) {
      alert("Failed to delete category");
    }
  };

  const handleCreateTag = async (e) => {
    e.preventDefault();
    if (!tagName || !selectedCategory) return;
    try {
      await api.post("/taxonomy/tags", { name: tagName, category_id: selectedCategory.id });
      setTagName("");
      fetchTags(selectedCategory.id);
    } catch (err) {
      alert("Failed to create tag: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteTag = async (id) => {
    try {
      await api.delete(`/taxonomy/tags/${id}`);
      fetchTags(selectedCategory.id);
    } catch (err) {
      alert("Failed to delete tag");
    }
  };

  return (
    <Layout>
      <div className="admin-page">
        <div className="admin-content">
        <h1>Taxonomy Management</h1>
        <p>Manage controlled vocabulary categories and tags for assets.</p>

        <div style={{ display: "flex", gap: "2rem", marginTop: "2rem" }}>
          {/* CATEGORIES COLUMN */}
          <div style={{ flex: 1, background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px" }}>
            <h2>Categories</h2>
            <form onSubmit={handleCreateCategory} style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
              <input
                type="text"
                placeholder="New Category Name"
                value={catName}
                onChange={(e) => setCatName(e.target.value)}
                required
                style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #333", background: "#2a2a2a", color: "#fff", flex: 1 }}
              />
              <button type="submit" style={{ padding: "0.5rem 1rem", background: "#4caf50", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}>Add</button>
            </form>
            <ul style={{ listStyle: "none", padding: 0 }}>
              {categories.map((c) => (
                <li
                  key={c.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    padding: "0.75rem",
                    marginBottom: "0.5rem",
                    background: selectedCategory?.id === c.id ? "#333" : "#222",
                    borderRadius: "4px",
                    cursor: "pointer"
                  }}
                  onClick={() => setSelectedCategory(c)}
                >
                  <span>{c.name}</span>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDeleteCategory(c.id); }}
                    style={{ background: "transparent", color: "#ff4444", border: "none", cursor: "pointer" }}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* TAGS COLUMN */}
          <div style={{ flex: 1, background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px" }}>
            <h2>Tags {selectedCategory ? `for ${selectedCategory.name}` : ""}</h2>
            {!selectedCategory ? (
              <p style={{ color: "#aaa" }}>Select a category to view and manage tags.</p>
            ) : (
              <>
                <form onSubmit={handleCreateTag} style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
                  <input
                    type="text"
                    placeholder="New Tag Name"
                    value={tagName}
                    onChange={(e) => setTagName(e.target.value)}
                    required
                    style={{ padding: "0.5rem", borderRadius: "4px", border: "1px solid #333", background: "#2a2a2a", color: "#fff", flex: 1 }}
                  />
                  <button type="submit" style={{ padding: "0.5rem 1rem", background: "#2196f3", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}>Add</button>
                </form>
                <ul style={{ listStyle: "none", padding: 0 }}>
                  {tags.map((t) => (
                    <li
                      key={t.id}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.75rem",
                        marginBottom: "0.5rem",
                        background: "#222",
                        borderRadius: "4px"
                      }}
                    >
                      <span>{t.name}</span>
                      <button
                        onClick={() => handleDeleteTag(t.id)}
                        style={{ background: "transparent", color: "#ff4444", border: "none", cursor: "pointer" }}
                      >
                        Delete
                      </button>
                    </li>
                  ))}
                  {tags.length === 0 && <p style={{ color: "#aaa" }}>No tags found in this category.</p>}
                </ul>
              </>
            )}
          </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default TaxonomyManagement;
