# app.py

# Import the viewer class from its location within the scripts package
from scripts._6_viewer import ModelViewer

# Standard Python entry point check
if __name__ == "__main__":
    # Create an instance of the ModelViewer
    viewer = ModelViewer()
    # Run the Streamlit interface
    viewer.run()
