
# Alternating Training of Learned Adversaries (ATLA) with SUMO- Robust Reinforcement Learning

This project implements the **Alternating Training of Learned Adversaries (ATLA)** approach in Reinforcement Learning (RL). It aims to train a defense agent while the adversary is fixed, and then train the adversary while the defense is fixed, alternating the training between both agents.

## Key Features

- **Alternating Training**: The defense agent and adversary take turns in training, with each agent learning to adapt to the other's actions.
- **SUMO Integration**: The environment is based on the SUMO traffic simulation, which models traffic signals, vehicles, and traffic management.
- **State and Reward Normalization**: Implemented support for state and reward normalization to stabilize training.
- **Custom Environment Wrapper**: The original SUMO environment is wrapped with additional features, such as normalization and time-based features.
- **Robust RL**: Focus on training agents in challenging environments where they must perform well against adversarial strategies.

## Project Setup

### 1. Cloning the Repository

To start using this project, first clone the repository to your local machine:

```bash
git clone https://github.com/Yizushdz/ATLAxSUMO.git
cd ATLAxSUMO
```

### 2. Setting up the Environment using the `environment.yml`

This project comes with an `environment.yml` file that contains all the dependencies required to run the project. You can quickly set up the environment by following these steps:

- **Using Conda**:

  If you have Conda installed, you can create a new environment with all the required dependencies by running the following command:

  ```bash
  conda create --name name-of-your-choice --file environment.yml
  ```

  This command will automatically create a new Conda environment with all the necessary dependencies, such as `gym`, `numpy`, `torch`, and others.

- **Activating the Environment**:

  Once the environment has been created, activate it by running:

  ```bash
  conda activate name-of-your-env
  ```

  Now, the environment is set up and ready to use! You can start running the project and training the agent.

- **Installing Conda (if not installed)**:

  If you don't have Conda installed, you can install it by downloading and installing [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/individual).

Now your environment is ready to go! Continue with the next steps to run or train the agent.

### 3. Running the Project

Once the environment is set up, you can run the project by executing the following command:

```bash
python main.py
```

This will start the RL training process using the ATLA approach. Make sure you have the necessary data files for the simulation.

### 4. Training the Agent

To train the agent, the project uses a custom environment wrapped around a SUMO (Simulation of Urban MObility) simulation. Make sure you have the necessary simulation files, such as `*.net.xml` and `*.rou.xml`, for the environment.

#### Training Configuration:

In the `agent.py` file, you can configure various training parameters, including:

- `norm_states`: Whether to normalize states.
- `norm_rewards`: The type of reward normalization ("rewards" or "returns").
- `clip_obs`: The clipping value for observations.
- `clip_rew`: The clipping value for rewards.
- `single_agent`: Whether to train in a single-agent setup or multi-agent setup.

## Project Advisor

This project is conducted under the guidance of [Dr. Mohamadhossein Noruzoliaee](https://www.utrgv.edu/cive/faculty/mohamadhossein-noruzoliaee/index.htm), a faculty member in the Department of Civil Engineering at The University of Texas Rio Grande Valley.

### 5. Credits

This project builds upon the original ATLA framework developed by [Huan Zhang](https://github.com/huanzhang12/ATLA_robust_RL). We would like to thank him for his contributions.

You can find the original project [here](https://github.com/huanzhang12/ATLA_robust_RL).
