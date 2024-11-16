<a name="readme-top"></a>

<br />
<div align="center">
  <a href="https://github.com/MickaelCormier/django-rbaca/blob/main/assets/rbaca_logo.jpg">
    <img src="assets/rbaca_logo.jpg" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">django-rbaca</h3>

  <p align="center">
    Role-based Access Control with Attributes for distributed Django projects.
    <br />
  </p>
</div>

## About The Project
Welcome to Role-Based Access Control with Attributes for distributed Django projects!

This project provides a secure and scalable solution for access control in Django applications. It extends the traditional role-based access control (RBAC) model with attributes to offer finer-grained control over resource access. The implementation is designed to allow decentralized nodes to have access to resources controlled by a central endpoint.

The project offers a Django app for easy integration into existing projects. It includes models for defining roles, attributes, access control policies, as well as an authorization backend for enforcing access control rules. The app also features an API for querying the access control system.

### Key Features
- **Role-based access control**: Users are assigned roles that define their access to resources.
- **Attribute-based access control**: Attributes are assigned to resources and users for finer-grained control over access.
- **Access control API for external nodes**: Centralized access control interface for decentralized nodes.
- **Easy integration**: The Django app is designed for seamless integration into existing projects.

## Installation

**Using pip (from PyPI):**

```bash
pip install django-rbaca
```

**Using poetry (local development):**

1. Clone the repository:

```bash
git clone https://github.com/MickaelCormier/django-rbaca
```

2. Navigate to the project directory:

```bash
cd django-rbaca
```

3. Install dependencies:

```bash
poetry install
```

## Documentation
For more detailed information, including prerequisites, configuration, and usage examples, please refer to the [documentation](url).

## Citation
If you find this project useful in your research, please consider cite:

```bash
@misc{django-rbaca,
    title={django-rbaca: Roll-based Access Control with Attributes for distributed Django projects.},
    author={Bruch, Steven and Cormier, Mickael},
    howpublished = {\url{https://github.com/MickaelCormier/django-rbaca/}},
    year={2024}
}
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>
