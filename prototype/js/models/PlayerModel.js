// Player Model - handles player data operations

class PlayerModel extends BaseModel {
    constructor() {
        super();
    }

    // Get all players
    getAllPlayers() {
        try {
            if (!this.mockData || !this.mockData.players) {
                return [];
            }
            return this.mockData.players;
        } catch (error) {
            return this.handleError(error, 'getAllPlayers');
        }
    }

    // Get active players only
    getActivePlayers() {
        try {
            const allPlayers = this.getAllPlayers();
            return allPlayers.filter(p => p.isActive);
        } catch (error) {
            return this.handleError(error, 'getActivePlayers');
        }
    }

    // Get player by ID
    getPlayerById(playerId) {
        try {
            const players = this.getAllPlayers();
            return players.find(p => p.playerId === playerId) || null;
        } catch (error) {
            return this.handleError(error, 'getPlayerById');
        }
    }

    // Get player by unique link
    getPlayerByLink(uniqueLink) {
        try {
            const players = this.getAllPlayers();
            return players.find(p => p.uniqueLink === uniqueLink) || null;
        } catch (error) {
            return this.handleError(error, 'getPlayerByLink');
        }
    }

    // Create new player
    createPlayer(playerData) {
        try {
            this.validateRequired(playerData, ['name', 'email', 'uniqueLink']);
            
            const newPlayer = {
                playerId: `player-${Date.now()}`,
                name: playerData.name,
                email: playerData.email,
                uniqueLink: playerData.uniqueLink,
                createdAt: new Date().toISOString(),
                isActive: playerData.isActive !== undefined ? playerData.isActive : true,
                teamId: playerData.teamId || 'team-001'
            };

            // In prototype, add to mock data
            if (this.mockData && this.mockData.players) {
                this.mockData.players.push(newPlayer);
            }

            return newPlayer;
        } catch (error) {
            return this.handleError(error, 'createPlayer');
        }
    }

    // Update player
    updatePlayer(playerId, updates) {
        try {
            const player = this.getPlayerById(playerId);
            if (!player) {
                throw new Error(`Player not found: ${playerId}`);
            }

            const updated = {
                ...player,
                ...updates,
                updatedAt: new Date().toISOString()
            };

            // In prototype, update in mock data
            if (this.mockData && this.mockData.players) {
                const index = this.mockData.players.findIndex(p => p.playerId === playerId);
                if (index !== -1) {
                    this.mockData.players[index] = updated;
                }
            }

            return updated;
        } catch (error) {
            return this.handleError(error, 'updatePlayer');
        }
    }

    // Delete player (soft delete by setting isActive to false)
    deletePlayer(playerId) {
        try {
            return this.updatePlayer(playerId, { isActive: false });
        } catch (error) {
            return this.handleError(error, 'deletePlayer');
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.PlayerModel = PlayerModel;
}

